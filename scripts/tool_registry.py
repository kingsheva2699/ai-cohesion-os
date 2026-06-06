#!/usr/bin/env python3
"""Manage public-safe tool module manifests for an AI Cohesion OS workspace.

The registry helps turn internal workflow modules into GitHub-ready tools without
accidentally publishing private customer data. It validates module metadata and
can scaffold README/MANIFEST/PRIVACY/VALIDATION files for a module folder.

Usage:
  python scripts/tool_registry.py ./my-ai-workspace init
  python scripts/tool_registry.py ./my-ai-workspace list
  python scripts/tool_registry.py ./my-ai-workspace check
  python scripts/tool_registry.py ./my-ai-workspace scaffold lead-intake-fast-reply
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_NAME = "tool_modules.json"
MODULE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
REQUIRED_FIELDS = ["id", "name", "purpose", "status", "repoName", "privacyLevel", "publicBoundary"]
ARTIFACT_REQUIRED_STATUSES = {"scaffolded", "active", "published"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def norm(text: str | Path) -> str:
    return str(text).replace("\\", "/").strip("/")


def config_path(workspace: Path) -> Path:
    return workspace.resolve() / "tools" / DEFAULT_CONFIG_NAME


def load_template_config() -> dict[str, Any]:
    return json.loads((ROOT / "templates" / DEFAULT_CONFIG_NAME).read_text(encoding="utf-8"))


def write_config(path: Path, config: dict[str, Any]) -> None:
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def init_config(workspace: Path, force: bool = False) -> Path:
    workspace = workspace.resolve()
    (workspace / "tools").mkdir(parents=True, exist_ok=True)
    target = config_path(workspace)
    if target.exists() and not force:
        return target
    write_config(target, load_template_config())
    return target


def load_config(workspace: Path) -> dict[str, Any]:
    path = config_path(workspace)
    if not path.exists():
        raise FileNotFoundError(f"Tool registry not found: {path}. Run: python scripts/tool_registry.py {workspace} init")
    return json.loads(path.read_text(encoding="utf-8"))


def module_by_id(config: dict[str, Any], module_id: str) -> dict[str, Any]:
    for module in config.get("modules", []):
        if module.get("id") == module_id:
            return module
    raise KeyError(f"Module not found in registry: {module_id}")


def ensure_inside(root: Path, candidate: Path) -> bool:
    root = root.resolve()
    candidate = candidate.resolve()
    return candidate == root or root in candidate.parents


def check_module(workspace: Path, module: dict[str, Any]) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    module_id = str(module.get("id", ""))

    for field in REQUIRED_FIELDS:
        if not str(module.get(field, "")).strip():
            errors.append(f"{module_id or '<missing-id>'}: missing required field `{field}`")

    if module_id and not MODULE_ID_RE.match(module_id):
        errors.append(f"{module_id}: id must be lowercase kebab-case, 3-64 chars")

    privacy = str(module.get("privacyLevel", "")).lower()
    if privacy in {"private", "raw-private-data", "customer-private"}:
        errors.append(f"{module_id}: privacyLevel `{privacy}` is not public-safe")
    elif privacy and privacy != "demo-data-only":
        warnings.append(f"{module_id}: privacyLevel `{privacy}` needs review before public release")

    if module.get("githubReady") and module.get("status") not in {"active", "published"}:
        warnings.append(f"{module_id}: githubReady=true but status is `{module.get('status')}`")

    artifacts = [norm(p) for p in module.get("artifacts", [])]
    if module.get("status") in ARTIFACT_REQUIRED_STATUSES:
        if not artifacts:
            errors.append(f"{module_id}: scaffolded/active/published module needs artifact paths")
        for rel_path in artifacts:
            target = (workspace / rel_path).resolve()
            if not ensure_inside(workspace, target):
                errors.append(f"{module_id}: artifact path escapes workspace: {rel_path}")
            elif not target.exists():
                errors.append(f"{module_id}: missing artifact: {rel_path}")
    else:
        for rel_path in artifacts:
            target = (workspace / rel_path).resolve()
            if not ensure_inside(workspace, target):
                errors.append(f"{module_id}: artifact path escapes workspace: {rel_path}")

    boundary = str(module.get("publicBoundary", "")).lower()
    if boundary and not any(word in boundary for word in ["never", "do not", "demo", "synthetic", "public"]):
        warnings.append(f"{module_id}: publicBoundary should explicitly say what must not be published")

    return warnings, errors


def check_registry(workspace: Path, as_json: bool = False) -> int:
    config = load_config(workspace)
    modules = config.get("modules", [])
    all_warnings: list[str] = []
    all_errors: list[str] = []

    seen: set[str] = set()
    for module in modules:
        module_id = str(module.get("id", ""))
        if module_id in seen:
            all_errors.append(f"duplicate module id: {module_id}")
        seen.add(module_id)
        warnings, errors = check_module(workspace.resolve(), module)
        all_warnings.extend(warnings)
        all_errors.extend(errors)

    result = {
        "checkedAt": now_iso(),
        "workspace": str(workspace.resolve()),
        "moduleCount": len(modules),
        "warnings": all_warnings,
        "errors": all_errors,
        "status": "fail" if all_errors else ("warn" if all_warnings else "pass"),
    }

    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Tool registry: {result['status']} ({len(modules)} modules)")
        for warning in all_warnings:
            print(f"WARN: {warning}")
        for error in all_errors:
            print(f"ERROR: {error}")
    return 1 if all_errors else 0


def list_modules(workspace: Path, as_json: bool = False) -> int:
    config = load_config(workspace)
    modules = config.get("modules", [])
    if as_json:
        print(json.dumps(modules, ensure_ascii=False, indent=2))
        return 0
    for module in modules:
        ready = "ready" if module.get("githubReady") else "not-ready"
        print(f"{module.get('id')} | {module.get('status')} | {ready} | repo={module.get('repoName')}")
    return 0


def markdown_readme(module: dict[str, Any]) -> str:
    return f"""# {module['name']}

A public-safe AI Cohesion OS tool module candidate.

## Purpose

{module['purpose']}

## Status

- Module ID: `{module['id']}`
- Proposed repo: `{module.get('repoName', '')}`
- Status: `{module.get('status', 'scaffolded')}`
- Privacy level: `{module.get('privacyLevel', '')}`

## Boundary

{module.get('publicBoundary', '')}

## What this tool should prove

- It can run on synthetic/demo data.
- It has a small, repeatable smoke test.
- It produces useful output without needing private customer files.
- It has clear human approval boundaries before any external action.

## GitHub readiness checklist

- [ ] README is understandable without private context.
- [ ] MANIFEST explains inputs, outputs, and safety boundaries.
- [ ] PRIVACY explains excluded data and demo-data-only rule.
- [ ] VALIDATION has a smoke test and expected output.
- [ ] No private client/customer data is committed.
- [ ] License selected.
"""


def privacy_doc(module: dict[str, Any]) -> str:
    return f"""# Privacy Boundary — {module['name']}

This module is intended to be public-safe.

## Allowed in public repo

- Synthetic demo data
- Public documentation
- Generic workflow examples
- Small sample inputs/outputs created for demonstration

## Not allowed in public repo

- Real customer or prospect data
- Emails, CRM exports, chat logs, calendar exports, phone numbers, compose URLs, browser/session artifacts
- Credentials, API keys, tokens, cookies, `.env` files, or private config
- Internal business reports unless rewritten as public-safe examples

## Module-specific boundary

{module.get('publicBoundary', '')}
"""


def validation_doc(module: dict[str, Any]) -> str:
    return f"""# Validation — {module['name']}

## Minimum public smoke test

1. Run the tool on synthetic/demo input.
2. Confirm it produces the expected output.
3. Confirm no external messages, submissions, or API writes happen by default.
4. Confirm generated files do not include secrets or real customer data.

## Expected proof before GitHub publish

- Command used
- Output summary
- Files created
- Privacy check result
- Known limitations
"""


def manifest_doc(module: dict[str, Any]) -> str:
    manifest = {
        "schemaVersion": "0.1",
        "generatedAt": now_iso(),
        "id": module["id"],
        "name": module["name"],
        "purpose": module["purpose"],
        "repoName": module.get("repoName"),
        "privacyLevel": module.get("privacyLevel"),
        "toolSurface": module.get("toolSurface"),
        "publicBoundary": module.get("publicBoundary"),
        "defaultExternalActions": "none",
        "requiresHumanApprovalFor": [
            "sending messages",
            "submitting forms/applications",
            "contacting customers/advisors/third parties",
            "publishing private or customer-specific data"
        ],
    }
    return json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"


def scaffold_module(workspace: Path, module_id: str, force: bool = False) -> int:
    workspace = workspace.resolve()
    config = load_config(workspace)
    module = module_by_id(config, module_id)
    module_dir = workspace / "tools" / module_id
    if not ensure_inside(workspace, module_dir):
        raise ValueError(f"Module path escapes workspace: {module_dir}")
    module_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "README.md": markdown_readme({**module, "status": "scaffolded"}),
        "MANIFEST.json": manifest_doc(module),
        "PRIVACY.md": privacy_doc(module),
        "VALIDATION.md": validation_doc(module),
    }
    for filename, content in files.items():
        target = module_dir / filename
        if target.exists() and not force:
            continue
        target.write_text(content, encoding="utf-8")

    module["status"] = "scaffolded"
    module["githubReady"] = False
    module["scaffoldedAt"] = now_iso()
    write_config(config_path(workspace), config)
    print(f"Scaffolded tool module `{module_id}` at {module_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Cohesion OS tool module registry")
    parser.add_argument("workspace", help="Workspace path")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Create tools/tool_modules.json from template")
    p_init.add_argument("--force", action="store_true")

    p_list = sub.add_parser("list", help="List modules")
    p_list.add_argument("--json", action="store_true")

    p_check = sub.add_parser("check", help="Validate registry and scaffolded artifacts")
    p_check.add_argument("--json", action="store_true")

    p_scaffold = sub.add_parser("scaffold", help="Create README/MANIFEST/PRIVACY/VALIDATION for one module")
    p_scaffold.add_argument("module_id")
    p_scaffold.add_argument("--force", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    workspace = Path(args.workspace)

    if args.command == "init":
        path = init_config(workspace, force=args.force)
        print(f"Tool registry initialized at {path}")
        return 0
    if args.command == "list":
        return list_modules(workspace, as_json=args.json)
    if args.command == "check":
        return check_registry(workspace, as_json=args.json)
    if args.command == "scaffold":
        return scaffold_module(workspace, args.module_id, force=args.force)
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
