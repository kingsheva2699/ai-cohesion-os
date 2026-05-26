# Smoke test

```bash
python scripts/init_workspace.py ./tmp-workspace
python scripts/context_index.py ./tmp-workspace build
python scripts/context_index.py ./tmp-workspace query "project profile" --top 3
python scripts/context_index.py ./tmp-workspace get README.md --lines 20
python scripts/weekly_report.py ./tmp-workspace
```
