#!/usr/bin/env python3
from pathlib import Path
import shutil
import sys
from datetime import date

ROOT = Path(__file__).resolve().parents[1]

WORKSPACE_DIRS = [
    'projects',
    'inbox',
    'reports',
    'memory',
    'templates',
    'systems',
    'connectors',
    'tools',
    '.cohesion',
]


def copy_template(name: str, target: Path):
    src = ROOT / 'templates' / name
    if src.exists() and not target.exists():
        shutil.copyfile(src, target)


def main():
    if len(sys.argv) < 2:
        print('Usage: python scripts/init_workspace.py <workspace-path>')
        return 2
    ws = Path(sys.argv[1]).resolve()
    ws.mkdir(parents=True, exist_ok=True)
    for d in WORKSPACE_DIRS:
        (ws / d).mkdir(exist_ok=True)
    copy_template('project_profile.md', ws / 'templates' / 'project_profile.md')
    copy_template('weekly_report.md', ws / 'templates' / 'weekly_report.md')
    copy_template('context_manifest.json', ws / 'templates' / 'context_manifest.json')
    copy_template('connectors.json', ws / 'connectors' / 'connectors.json')
    copy_template('tool_modules.json', ws / 'tools' / 'tool_modules.json')
    copy_template('decision_log.md', ws / 'memory' / 'decision_log.md')
    readme = ws / 'README.md'
    if not readme.exists():
        readme.write_text(f'''# Project Memory Workspace

Created: {date.today()}

## Folders

- `projects/` - one folder per project
- `inbox/` - raw notes to sort
- `reports/` - weekly/monthly reports
- `memory/` - decision logs and durable context
- `templates/` - reusable templates
- `systems/` - local exports/events from customer systems
- `connectors/` - connector health configuration
- `tools/` - public-safe tool module manifests and scaffolds
- `.cohesion/` - generated local context indexes and health reports (do not publish private indexes)

## Next step

Create a project folder and copy `templates/project_profile.md` into it. Then run:

```bash
python scripts/context_index.py . build
python scripts/connector_health.py . check --write
python scripts/tool_registry.py . check
```
''', encoding='utf-8')
    print(f'Initialized Project Memory workspace at {ws}')


if __name__ == '__main__':
    raise SystemExit(main())
