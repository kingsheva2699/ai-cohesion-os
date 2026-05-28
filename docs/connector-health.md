# Connector Health

AI Cohesion OS now includes a local-first connector health system.

The goal is not to pretend the starter kit already has live Gmail/Slack/CRM integrations. The goal is to make the communication protocol testable immediately:

1. Customer systems export normalized events or records into `systems/`.
2. `connectors/connectors.json` defines which exports/probes are expected.
3. `scripts/connector_health.py` checks presence, freshness, and optional HTTP health probes.
4. Health output is written to `.cohesion/connector_health.json` and `reports/connector_health_DATE.md`.
5. AI tools can use the health report before trusting a connector's context.

## Quick start

```bash
python scripts/init_workspace.py ./my-ai-workspace
python scripts/connector_health.py ./my-ai-workspace check --write
```

A brand-new workspace will usually show degraded/failing connectors until you add system exports.

## Expected local export layout

The default `templates/connectors.json` expects:

```text
my-ai-workspace/
  systems/
    email/messages.jsonl
    crm/*.csv
    calendar/*.md
    chat/*.md
    webhooks/*.jsonl
  connectors/connectors.json
```

These are intentionally boring formats. They are easy for humans, scripts, AI assistants, Zapier/Make, cron jobs, browser exports, and future live connectors to produce.

## Example connector config

```json
{
  "id": "crm_export",
  "name": "CRM / pipeline export",
  "type": "file_export",
  "enabled": true,
  "critical": true,
  "requiredPaths": ["systems/crm/*.csv"],
  "freshnessHours": 48
}
```

Optional HTTP probes can be added for systems you control:

```json
{
  "id": "internal_webhook_relay",
  "name": "Internal webhook relay",
  "type": "http_probe",
  "enabled": true,
  "critical": false,
  "requiredPaths": ["systems/webhooks/*.jsonl"],
  "healthUrl": "http://127.0.0.1:8080/health",
  "expectedStatus": 200,
  "timeoutSeconds": 3,
  "freshnessHours": 24
}
```

## CLI

```bash
# Create connectors/connectors.json from the template if missing
python scripts/connector_health.py ./my-ai-workspace init

# Check health and print text output
python scripts/connector_health.py ./my-ai-workspace check

# Write machine + human reports
python scripts/connector_health.py ./my-ai-workspace check --write

# Print JSON for automation
python scripts/connector_health.py ./my-ai-workspace check --json

# Do not fail shell scripts even when connectors are degraded/failing
python scripts/connector_health.py ./my-ai-workspace check --soft
```

## Status model

- `healthy` — enabled connector has required exports/probes and freshness is acceptable.
- `degraded` — non-critical connector is missing, stale, or probe-failing; or any connector has stale exports.
- `failing` — critical connector is missing required exports or has a failed health probe.
- `disabled` — explicitly disabled in config.

The command exits non-zero when overall status is `degraded` or `failing`, unless `--soft` is used.

## What this validates

The starter kit can now honestly validate:

- setup creates connector configuration;
- customer-system exports are present;
- exports are fresh enough;
- optional probes are reachable;
- generated reports expose connector state;
- AI tools have a health gate before trusting system context.

## What this does not claim yet

This is still not a full live integration layer. It does not yet provide OAuth, background sync, retry queues, bidirectional sending, webhook servers, or vendor-specific API clients.

That is the right boundary for a starter kit: prove the protocol and health gate first, then add live adapters behind the same contract.

## Privacy boundary

- Do not put credentials in `systems/`.
- Prefer summaries/manifests over raw private attachments.
- Keep `.env` and credential files excluded from indexing.
- Human approval is still required before external sends or public actions.
