#!/usr/bin/env python3
from pathlib import Path
import sys
from datetime import date


def main():
    if len(sys.argv) < 2:
        print('Usage: python scripts/weekly_report.py <workspace-path>')
        return 2
    ws = Path(sys.argv[1]).resolve()
    projects = sorted((ws / 'projects').glob('*')) if (ws / 'projects').exists() else []
    report_dir = ws / 'reports'
    report_dir.mkdir(exist_ok=True)
    out = report_dir / f'weekly_report_{date.today().isoformat()}.md'
    lines = [f'# Weekly Project Health Report — {date.today()}', '']
    lines += ['## Projects found', '']
    if not projects:
        lines.append('- No project folders found yet.')
    for p in projects:
        if p.is_dir():
            profile = p / 'project_profile.md'
            status = 'profile exists' if profile.exists() else 'missing project_profile.md'
            lines.append(f'- **{p.name}** — {status}')
    lines += ['', '## Recommended next actions', '', '1. Add/update project profiles.', '2. Fill open loops and decisions.', '3. Re-run this report weekly.', '']
    out.write_text('\n'.join(lines), encoding='utf-8')
    print(out)

if __name__ == '__main__':
    raise SystemExit(main())
