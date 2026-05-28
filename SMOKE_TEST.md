# Smoke test

```bash
python scripts/init_workspace.py ./tmp-workspace
mkdir -p ./tmp-workspace/systems/email ./tmp-workspace/systems/crm ./tmp-workspace/systems/calendar ./tmp-workspace/systems/chat ./tmp-workspace/systems/webhooks
printf '{"event":"message.received","subject":"Test lead"}\n' > ./tmp-workspace/systems/email/messages.jsonl
printf 'id,name,status\n1,Test Lead,new\n' > ./tmp-workspace/systems/crm/leads.csv
printf '# Calendar\n- Follow up with Test Lead\n' > ./tmp-workspace/systems/calendar/events.md
printf '# Chat\nOps note: Test Lead needs response.\n' > ./tmp-workspace/systems/chat/ops.md
printf '{"event":"lead.created","lead_id":"1"}\n' > ./tmp-workspace/systems/webhooks/events.jsonl
python scripts/connector_health.py ./tmp-workspace check --write
python scripts/context_index.py ./tmp-workspace build
python scripts/context_index.py ./tmp-workspace query "project profile" --top 3
python scripts/context_index.py ./tmp-workspace get README.md --lines 20
python scripts/weekly_report.py ./tmp-workspace
```
