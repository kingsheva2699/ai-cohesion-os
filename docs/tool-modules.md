# Tool Modules

AI Cohesion OS can turn internal workflow modules into public-safe tools without mixing in private customer context.

This layer is for operators who want to build reusable AI workflow tools from real operating patterns, then publish them as GitHub repos only after they are clean, demo-data-only, and validated.

## Why this exists

Internal AI systems often produce useful modules:

- lead intake triage
- follow-up/status radar
- workflow briefings
- approval checklists
- connector health checks
- evidence logs
- customer process mappers

Those modules can become public proof, client demos, starter kits, or open-source tools. The risk is accidentally publishing private data or building a vague repo with no validation.

The tool module layer adds structure before publishing:

1. Register the module.
2. Declare the public boundary.
3. Scaffold README / MANIFEST / PRIVACY / VALIDATION files.
4. Validate the registry.
5. Only then create/push a public GitHub repo.

## Commands

Initialize a workspace registry:

```bash
python scripts/tool_registry.py ./my-ai-workspace init
```

List modules:

```bash
python scripts/tool_registry.py ./my-ai-workspace list
```

Scaffold a module:

```bash
python scripts/tool_registry.py ./my-ai-workspace scaffold lead-intake-fast-reply
```

Validate registry and scaffolded artifacts:

```bash
python scripts/tool_registry.py ./my-ai-workspace check
```

## Registry file

The default registry lives at:

```text
my-ai-workspace/tools/tool_modules.json
```

Each module should define:

- `id` — lowercase kebab-case module ID
- `name` — human-readable tool name
- `purpose` — what the tool proves
- `status` — `candidate`, `scaffolded`, `active`, or `published`
- `repoName` — proposed GitHub repository name
- `privacyLevel` — usually `demo-data-only`
- `publicBoundary` — explicit rule for what must not be published
- `artifacts` — README/MANIFEST/PRIVACY/VALIDATION paths

## Default candidate modules

The template starts with three generic AI workflow modules:

1. `lead-intake-fast-reply` — triage messy inbound leads and prepare a human-approved reply.
2. `client-status-radar` — summarize customer/project state, open loops, and next action.
3. `workflow-briefing-layer` — turn scattered process notes into daily briefings and blockers.

These are examples, not private customer systems. Use synthetic/demo data only.

## Public GitHub readiness

A module is not GitHub-ready just because it has a folder.

Minimum checklist:

- README is understandable without private context.
- MANIFEST defines inputs, outputs, boundaries, and default external actions.
- PRIVACY explains exactly what is excluded.
- VALIDATION includes a smoke test with synthetic/demo data.
- No client/customer files, emails, CRM exports, phone numbers, compose links, credentials, logs, or private reports.
- The module can run locally without requiring secret accounts.
- Any external write — email, message, submission, advisor contact, payment, or publication — requires explicit human approval.

## Relationship to Cohesion OS

Cohesion OS is the operating layer:

- project tracing
- context serving
- connector health
- tool module registry

The public tool repos are the visible artifacts built on top of that layer.

In other words: Cohesion OS keeps the system coherent; tool modules become the proof and reusable surface.
