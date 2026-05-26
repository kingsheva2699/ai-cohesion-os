#!/usr/bin/env python3
"""Build and query a small local context index for an AI Cohesion OS workspace.

This is intentionally simple and dependency-free. It turns project files into
bounded context chunks so an AI assistant can load the smallest useful slice
instead of rereading whole folders or relying on chat history.

Usage:
  python scripts/context_index.py ./my-ai-workspace build
  python scripts/context_index.py ./my-ai-workspace query "open loops" --top 5
  python scripts/context_index.py ./my-ai-workspace get projects/example/project_profile.md --lines 80
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

TEXT_EXTS = {
    ".md", ".txt", ".json", ".jsonl", ".csv", ".py", ".js", ".ts",
    ".html", ".css", ".yml", ".yaml", ".toml", ".ini",
}
EXCLUDE_GLOBS = [
    ".git", ".git/**", "**/.git/**", "node_modules", "**/node_modules/**",
    ".venv", "venv", "**/.venv/**", "**/venv/**", "__pycache__", "**/__pycache__/**",
    ".cohesion/context_index.json", ".cohesion/context_chunks.json",
    "**/*.zip", "**/*.db", "**/*.sqlite", "**/*.sqlite3", "**/*.log",
    "**/*.png", "**/*.jpg", "**/*.jpeg", "**/*.gif", "**/*.webp", "**/*.pdf", "**/*.xlsx",
    "**/*secret*", "**/*credential*", "**/*.key", "**/*.pem", ".env", ".env.*",
]
TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_+.-]*", re.I)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
CHUNK_TARGET_CHARS = 2400
CHUNK_OVERLAP_LINES = 3


def tokens(text: str) -> set[str]:
    return {t.lower() for t in TOKEN_RE.findall(text or "") if len(t) > 1}


def norm(path: str | Path) -> str:
    return str(path).replace("\\", "/").strip("/")


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def is_excluded(root: Path, path: Path) -> bool:
    r = norm(rel(root, path))
    base = path.name
    for pat in EXCLUDE_GLOBS:
        p = norm(pat)
        if fnmatch.fnmatch(r, p) or fnmatch.fnmatch(base, p):
            return True
    return False


def safe_read(path: Path) -> str:
    return path.read_bytes()[:750_000].decode("utf-8", errors="replace")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def infer_title(path: Path, text: str) -> str:
    for line in text.splitlines()[:20]:
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.strip("# ")[:160]
    return path.stem.replace("_", " ").replace("-", " ").title()


@dataclass
class FileRecord:
    path: str
    title: str
    ext: str
    size: int
    mtime: float
    sha256: str
    headings: list[str]
    snippet: str


@dataclass
class ChunkRecord:
    chunkId: str
    path: str
    startLine: int
    endLine: int
    title: str
    heading: str
    text: str
    snippet: str


def split_lines(lines: list[str], start_line: int, title: str, path: str) -> list[ChunkRecord]:
    out: list[ChunkRecord] = []
    i = 0
    while i < len(lines):
        j = i
        chars = 0
        while j < len(lines) and (chars < CHUNK_TARGET_CHARS or j == i):
            chars += len(lines[j]) + 1
            j += 1
        if j < len(lines):
            floor = i + max(1, (j - i) * 2 // 3)
            for k in range(j - 1, floor, -1):
                if not lines[k].strip():
                    j = k + 1
                    break
        text = "\n".join(lines[i:j]).strip()
        if text:
            start = start_line + i
            end = start_line + j - 1
            out.append(ChunkRecord(
                chunkId=f"{path}#L{start}-L{end}",
                path=path,
                startLine=start,
                endLine=end,
                title=title,
                heading=title,
                text=text,
                snippet=text[:500],
            ))
        if j >= len(lines):
            break
        i = max(j - CHUNK_OVERLAP_LINES, i + 1)
    return out


def chunk_file(path: Path, rel_path: str, text: str, title: str) -> list[ChunkRecord]:
    lines = text.splitlines()
    if not lines:
        return []
    headings: list[tuple[int, str]] = []
    if path.suffix.lower() == ".md":
        for idx, line in enumerate(lines):
            m = HEADING_RE.match(line)
            if m:
                headings.append((idx, m.group(2).strip()))
    chunks: list[ChunkRecord] = []
    if headings:
        if headings[0][0] > 0:
            chunks.extend(split_lines(lines[:headings[0][0]], 1, title, rel_path))
        for n, (idx, heading) in enumerate(headings):
            next_idx = headings[n + 1][0] if n + 1 < len(headings) else len(lines)
            chunks.extend(split_lines(lines[idx:next_idx], idx + 1, heading, rel_path))
    else:
        chunks.extend(split_lines(lines, 1, title, rel_path))
    return chunks


def build(root: Path) -> dict[str, Any]:
    root = root.resolve()
    cohesion = root / ".cohesion"
    cohesion.mkdir(exist_ok=True)
    files: list[FileRecord] = []
    chunks: list[ChunkRecord] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTS or is_excluded(root, path):
            continue
        text = safe_read(path)
        r = rel(root, path)
        headings = [m.group(2).strip() for line in text.splitlines() if (m := HEADING_RE.match(line))][:50]
        title = headings[0] if headings else infer_title(path, text)
        stat = path.stat()
        files.append(FileRecord(
            path=r,
            title=title,
            ext=path.suffix.lower(),
            size=stat.st_size,
            mtime=stat.st_mtime,
            sha256=sha256(path) if stat.st_size < 750_000 else f"large:{stat.st_size}",
            headings=headings,
            snippet=text[:700],
        ))
        chunks.extend(chunk_file(path, r, text, title))
    index = {
        "version": 1,
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "workspaceRoot": str(root),
        "fileCount": len(files),
        "files": [asdict(x) for x in files],
    }
    chunk_index = {
        "version": 1,
        "generatedAt": index["generatedAt"],
        "workspaceRoot": str(root),
        "chunkTargetChars": CHUNK_TARGET_CHARS,
        "chunkCount": len(chunks),
        "chunks": [asdict(x) for x in chunks],
    }
    (cohesion / "context_index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    (cohesion / "context_chunks.json").write_text(json.dumps(chunk_index, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"index": index, "chunks": chunk_index}


def load(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    cohesion = root.resolve() / ".cohesion"
    index_path = cohesion / "context_index.json"
    chunk_path = cohesion / "context_chunks.json"
    if not index_path.exists() or not chunk_path.exists():
        built = build(root)
        return built["index"], built["chunks"]
    return json.loads(index_path.read_text(encoding="utf-8")), json.loads(chunk_path.read_text(encoding="utf-8"))


def score(query: str, row: dict[str, Any]) -> float:
    q = tokens(query)
    if not q:
        return 0.0
    weighted = {
        "path": 5.0,
        "title": 4.0,
        "heading": 5.0,
        "headings": 3.0,
        "text": 1.0,
        "snippet": 1.0,
    }
    total = 0.0
    for key, weight in weighted.items():
        value = row.get(key, "")
        if isinstance(value, list):
            value = " ".join(value)
        total += len(q & tokens(str(value))) * weight
    if query.lower() in row.get("path", "").lower() or query.lower() in row.get("title", "").lower():
        total += 12
    return total


def query(root: Path, q: str, top: int) -> list[dict[str, Any]]:
    _, chunk_index = load(root)
    results = []
    for chunk in chunk_index.get("chunks", []):
        s = score(q, chunk)
        if s > 0:
            item = dict(chunk)
            item["score"] = round(s, 2)
            item["text"] = item.get("text", "")[:CHUNK_TARGET_CHARS]
            results.append(item)
    results.sort(key=lambda x: (-x["score"], x.get("path", ""), x.get("startLine", 0)))
    return results[:top]


def bounded_get(root: Path, path_text: str, start: int, lines: int) -> dict[str, Any]:
    root = root.resolve()
    path = (root / norm(path_text)).resolve()
    if root not in path.parents and path != root:
        raise ValueError("Path escapes workspace")
    if not path.exists() or not path.is_file() or is_excluded(root, path):
        raise FileNotFoundError(path_text)
    text_lines = safe_read(path).splitlines()
    start = max(1, start)
    end = min(len(text_lines), start + max(1, lines) - 1)
    return {
        "path": rel(root, path),
        "start": start,
        "end": end,
        "totalLines": len(text_lines),
        "text": "\n".join(text_lines[start - 1:end]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build/query local AI Cohesion OS context chunks")
    parser.add_argument("workspace", help="Workspace path")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    q = sub.add_parser("query")
    q.add_argument("query")
    q.add_argument("--top", type=int, default=8)
    q.add_argument("--json", action="store_true")
    g = sub.add_parser("get")
    g.add_argument("path")
    g.add_argument("--start", type=int, default=1)
    g.add_argument("--lines", type=int, default=100)
    g.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = Path(args.workspace)
    if args.cmd == "build":
        out = build(root)
        print(f"indexed files={out['index']['fileCount']} chunks={out['chunks']['chunkCount']}")
        print(root.resolve() / ".cohesion")
    elif args.cmd == "query":
        results = query(root, args.query, args.top)
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            for i, r in enumerate(results, 1):
                print(f"{i}. [{r['score']}] {r['path']}:{r['startLine']}-{r['endLine']} - {r['heading']}")
                print("   " + re.sub(r"\s+", " ", r.get("snippet", "")[:280]))
    elif args.cmd == "get":
        out = bounded_get(root, args.path, args.start, args.lines)
        if args.json:
            print(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            print(f"--- {out['path']}:{out['start']}-{out['end']} / {out['totalLines']} ---")
            print(out["text"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
