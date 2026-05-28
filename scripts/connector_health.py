#!/usr/bin/env python3
"""Check AI Cohesion OS connector health.

The starter kit stays local-first: connectors can begin as file exports from
email, CRM, calendar, chat, forms, or webhooks. This script verifies that those
exports exist, are fresh enough, and optionally that HTTP health probes respond.

Usage:
  python scripts/connector_health.py ./my-ai-workspace init
  python scripts/connector_health.py ./my-ai-workspace check --write
  python scripts/connector_health.py ./my-ai-workspace check --json
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import sys
import time
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_NAME = "connectors.json"
DEFAULT_TIMEOUT_SECONDS = 5


@dataclass
class PathCheck:
    pattern: str
    matched: bool
    paths: list[str]
    newestAgeHours: float | None
    stale: bool
    message: str


@dataclass
class HttpCheck:
    url: str
    ok: bool
    status: int | None
    expectedStatus: int
    elapsedMs: int | None
    message: str


@dataclass
class ConnectorResult:
    id: str
    name: str
    type: str
    enabled: bool
    critical: bool
    status: str
    requiredPathChecks: list[PathCheck]
    optionalPathChecks: list[PathCheck]
    httpCheck: HttpCheck | None
    freshnessHours: float | None
    messages: list[str]
    nextAction: str


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def norm(text: str | Path) -> str:
    return str(text).replace("\\", "/").strip("/")


def load_template_config() -> dict[str, Any]:
    template = ROOT / "templates" / DEFAULT_CONFIG_NAME
    return json.loads(template.read_text(encoding="utf-8"))


def config_path(workspace: Path) -> Path:
    return workspace.resolve() / "connectors" / DEFAULT_CONFIG_NAME


def init_config(workspace: Path, force: bool = False) -> Path:
    workspace = workspace.resolve()
    (workspace / "connectors").mkdir(parents=True, exist_ok=True)
    target = config_path(workspace)
    if target.exists() and not force:
        return target
    target.write_text(json.dumps(load_template_config(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def load_config(workspace: Path) -> dict[str, Any]:
    path = config_path(workspace)
    if not path.exists():
        raise FileNotFoundError(f"Connector config not found: {path}. Run: python scripts/connector_health.py {workspace} init")
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_inside(root: Path, candidate: Path) -> bool:
    root = root.resolve()
    candidate = candidate.resolve()
    return candidate == root or root in candidate.parents


def glob_relative(root: Path, pattern: str) -> list[Path]:
    pattern = norm(pattern)
    if ".." in Path(pattern).parts:
        return []
    # Fast path for exact files.
    exact = (root / pattern).resolve()
    has_glob = any(ch in pattern for ch in "*?[")
    if not has_glob:
        return [exact] if ensure_inside(root, exact) and exact.exists() and exact.is_file() else []
    matches = []
    for path in root.rglob("*"):
        if not path.is_file() or not ensure_inside(root, path):
            continue
        if fnmatch.fnmatch(rel(root, path), pattern):
            matches.append(path)
    return sorted(matches)


def check_path_pattern(root: Path, pattern: str, freshness_hours: float | None, required: bool) -> PathCheck:
    matches = glob_relative(root, pattern)
    if not matches:
        return PathCheck(
            pattern=pattern,
            matched=False,
            paths=[],
            newestAgeHours=None,
            stale=False,
            message=("missing required path" if required else "optional path not present"),
        )
    now = time.time()
    newest_age = min((now - path.stat().st_mtime) / 3600 for path in matches)
    stale = bool(freshness_hours is not None and newest_age > freshness_hours)
    return PathCheck(
        pattern=pattern,
        matched=True,
        paths=[rel(root, path) for path in matches[:20]],
        newestAgeHours=round(newest_age, 2),
        stale=stale,
        message=(f"freshest file age {newest_age:.2f}h" + ("; stale" if stale else "")),
    )


def check_http(url: str, expected_status: int, timeout_seconds: float) -> HttpCheck:
    start = time.perf_counter()
    try:
        req = urllib.request.Request(url, headers={"user-agent": "ai-cohesion-os-connector-health/0.3"})
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            status = int(response.status)
            elapsed = int((time.perf_counter() - start) * 1000)
            return HttpCheck(
                url=url,
                ok=status == expected_status,
                status=status,
                expectedStatus=expected_status,
                elapsedMs=elapsed,
                message=f"HTTP {status} in {elapsed}ms",
            )
    except Exception as exc:  # noqa: BLE001 - dependency-free health script should report any probe failure.
        elapsed = int((time.perf_counter() - start) * 1000)
        return HttpCheck(
            url=url,
            ok=False,
            status=None,
            expectedStatus=expected_status,
            elapsedMs=elapsed,
            message=f"HTTP probe failed: {exc}",
        )


def evaluate_connector(root: Path, connector: dict[str, Any]) -> ConnectorResult:
    enabled = bool(connector.get("enabled", True))
    critical = bool(connector.get("critical", False))
    freshness = connector.get("freshnessHours")
    freshness_hours = float(freshness) if freshness is not None else None
    required_paths = list(connector.get("requiredPaths") or [])
    optional_paths = list(connector.get("optionalPaths") or [])
    messages: list[str] = []

    if not enabled:
        return ConnectorResult(
            id=str(connector.get("id", "unknown")),
            name=str(connector.get("name", connector.get("id", "unknown"))),
            type=str(connector.get("type", "unknown")),
            enabled=False,
            critical=critical,
            status="disabled",
            requiredPathChecks=[],
            optionalPathChecks=[],
            httpCheck=None,
            freshnessHours=freshness_hours,
            messages=["connector disabled in config"],
            nextAction="Enable the connector when this system should participate in the protocol.",
        )

    required_checks = [check_path_pattern(root, pattern, freshness_hours, True) for pattern in required_paths]
    optional_checks = [check_path_pattern(root, pattern, freshness_hours, False) for pattern in optional_paths]

    http = None
    if connector.get("healthUrl"):
        http = check_http(
            str(connector["healthUrl"]),
            int(connector.get("expectedStatus", 200)),
            float(connector.get("timeoutSeconds", DEFAULT_TIMEOUT_SECONDS)),
        )

    missing_required = [check for check in required_checks if not check.matched]
    stale_required = [check for check in required_checks if check.stale]
    stale_optional = [check for check in optional_checks if check.stale]
    http_failed = bool(http and not http.ok)

    if missing_required:
        messages.extend(f"missing {check.pattern}" for check in missing_required)
    if stale_required:
        messages.extend(f"stale required export {check.pattern}" for check in stale_required)
    if stale_optional:
        messages.extend(f"stale optional export {check.pattern}" for check in stale_optional)
    if http_failed and http:
        messages.append(http.message)

    if missing_required or http_failed:
        status = "failing" if critical else "degraded"
        next_action = "Restore the missing/probe-failing connector before relying on this system for live workflow context."
    elif stale_required or stale_optional:
        status = "degraded"
        next_action = "Refresh stale connector exports and re-run connector health."
    else:
        status = "healthy"
        next_action = "No action required; keep this export/probe refreshed on schedule."
        messages.append("all required connector checks passed")

    return ConnectorResult(
        id=str(connector.get("id", "unknown")),
        name=str(connector.get("name", connector.get("id", "unknown"))),
        type=str(connector.get("type", "unknown")),
        enabled=enabled,
        critical=critical,
        status=status,
        requiredPathChecks=required_checks,
        optionalPathChecks=optional_checks,
        httpCheck=http,
        freshnessHours=freshness_hours,
        messages=messages,
        nextAction=next_action,
    )


def summarize(results: list[ConnectorResult]) -> dict[str, int]:
    out = {"healthy": 0, "degraded": 0, "failing": 0, "disabled": 0}
    for result in results:
        out[result.status] = out.get(result.status, 0) + 1
    return out


def check(workspace: Path) -> dict[str, Any]:
    workspace = workspace.resolve()
    config = load_config(workspace)
    connectors = list(config.get("connectors") or [])
    results = [evaluate_connector(workspace, connector) for connector in connectors]
    summary = summarize(results)
    overall = "failing" if summary.get("failing") else "degraded" if summary.get("degraded") else "healthy"
    return {
        "version": 1,
        "generatedAt": now_iso(),
        "workspaceRoot": str(workspace),
        "configPath": rel(workspace, config_path(workspace)),
        "overallStatus": overall,
        "summary": summary,
        "connectors": [asdict(result) for result in results],
        "protocolBoundary": "Connector health verifies local exports/probes and protocol readiness; it does not grant permission for external sends or bypass human approval.",
    }


def write_outputs(workspace: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    workspace = workspace.resolve()
    cohesion = workspace / ".cohesion"
    reports = workspace / "reports"
    cohesion.mkdir(exist_ok=True)
    reports.mkdir(exist_ok=True)
    json_path = cohesion / "connector_health.json"
    md_path = reports / f"connector_health_{datetime.now().date().isoformat()}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Connector Health Report — {report['generatedAt']}",
        "",
        f"Overall status: **{report['overallStatus'].upper()}**",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: {value}")
    lines += ["", "## Connectors", ""]
    for connector in report["connectors"]:
        lines += [
            f"### {connector['name']}",
            "",
            f"- ID: `{connector['id']}`",
            f"- Type: `{connector['type']}`",
            f"- Status: **{connector['status']}**",
            f"- Critical: `{connector['critical']}`",
            f"- Next action: {connector['nextAction']}",
            "- Messages:",
        ]
        for message in connector["messages"]:
            lines.append(f"  - {message}")
        if connector["requiredPathChecks"]:
            lines += ["- Required paths:"]
            for check in connector["requiredPathChecks"]:
                paths = ", ".join(f"`{path}`" for path in check["paths"][:5]) or "none"
                lines.append(f"  - `{check['pattern']}` — {check['message']} — {paths}")
        if connector.get("httpCheck"):
            http = connector["httpCheck"]
            lines.append(f"- HTTP probe: `{http['url']}` — {http['message']}")
        lines.append("")
    lines += ["## Boundary", "", report["protocolBoundary"], ""]
    return "\n".join(lines)


def print_text(report: dict[str, Any]) -> None:
    print(f"overall={report['overallStatus']}")
    print("summary=" + ", ".join(f"{k}:{v}" for k, v in report["summary"].items()))
    for connector in report["connectors"]:
        print(f"{connector['status'].upper():9} {connector['id']} - {connector['name']}")
        for message in connector["messages"][:3]:
            print(f"  - {message}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check AI Cohesion OS connector health")
    parser.add_argument("workspace", help="Workspace path")
    sub = parser.add_subparsers(dest="cmd", required=True)
    init = sub.add_parser("init", help="Create connectors/connectors.json from the template")
    init.add_argument("--force", action="store_true", help="Overwrite existing connector config")
    chk = sub.add_parser("check", help="Evaluate connector health")
    chk.add_argument("--json", action="store_true", help="Print JSON report")
    chk.add_argument("--write", action="store_true", help="Write .cohesion/connector_health.json and reports/connector_health_DATE.md")
    chk.add_argument("--soft", action="store_true", help="Always exit 0 even if health is degraded/failing")
    args = parser.parse_args()
    workspace = Path(args.workspace)

    if args.cmd == "init":
        path = init_config(workspace, force=args.force)
        print(path)
        return 0

    if args.cmd == "check":
        report = check(workspace)
        if args.write:
            json_path, md_path = write_outputs(workspace, report)
            report["written"] = {"json": str(json_path), "markdown": str(md_path)}
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print_text(report)
            if args.write:
                print(f"wrote {report['written']['json']}")
                print(f"wrote {report['written']['markdown']}")
        if args.soft:
            return 0
        return 1 if report["overallStatus"] in {"degraded", "failing"} else 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
