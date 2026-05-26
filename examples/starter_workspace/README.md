# Project Memory Workspace

Created: 2026-05-19

## Folders

- `projects/` - one folder per project
- `inbox/` - raw notes to sort
- `reports/` - weekly/monthly reports
- `memory/` - decision logs and durable context
- `templates/` - reusable templates
- `.cohesion/` - generated local context indexes (do not publish private indexes)

## Next step

Create a project folder and copy `templates/project_profile.md` into it. Then run:

```bash
python scripts/context_index.py . build
```
