# Changelog

## Unreleased - Tool module layer

Starter kit update focused on turning internal workflow patterns into public-safe GitHub/tool modules.

### Added

- `scripts/tool_registry.py` for tool module registry init/list/check/scaffold.
- `templates/tool_modules.json` with starter candidate modules for lead intake, client status radar, and workflow briefing.
- Workspace `tools/` folder in `init_workspace.py`.
- `docs/tool-modules.md` explaining public GitHub readiness, privacy boundaries, and scaffolded artifacts.
- README and smoke-test coverage for the tool registry.

### Safety

- Tool modules default to `demo-data-only` and require explicit public boundaries.
- Scaffolded modules include README, MANIFEST, PRIVACY, and VALIDATION files before public publishing.
- The registry is metadata/scaffolding only; it does not create GitHub repos or push public code by itself.

## v0.3.0 - Connector health layer

Starter kit update focused on proving the customer-system communication protocol before adding live vendor connectors.

### Added

- `scripts/connector_health.py` for dependency-free connector health checks.
- `templates/connectors.json` with default email, CRM, calendar, chat, and webhook export checks.
- Workspace `systems/` and `connectors/` folders in `init_workspace.py`.
- `.cohesion/connector_health.json` machine-readable health report.
- `reports/connector_health_DATE.md` human-readable health report.
- `docs/connector-health.md` explaining local export health, optional HTTP probes, status model, and boundaries.
- GitHub Actions smoke test now validates connector health with mock customer-system exports.

### Changed

- README quick start now includes connector health initialization/checks.
- Smoke test now populates mock system exports before building the context index.
- Context index excludes generated `.cohesion/connector_health.json` while allowing the Markdown report to be indexed.

### Safety

- Connector health verifies local exports/probes only; it does not grant permission for external sends.
- Default config warns against credentials/raw private attachments in `systems/`.

## v0.2.0 - Context serving layer

Public-safe starter kit update focused on efficient AI context use.

### Added

- `scripts/context_index.py` for local dependency-free context indexing.
- `.cohesion/context_index.json` and `.cohesion/context_chunks.json` generation.
- Chunk search command for small source-linked sections.
- Bounded excerpt command for exact file/line retrieval.
- `docs/context-serving.md` explaining retrieval discipline and safety defaults.
- `templates/context_manifest.json` as an optional routing hint template.
- `.cohesion/` workspace folder creation in `init_workspace.py`.

### Changed

- README now frames context serving as the v0.2 proof point for AI cohesion.
- Architecture now includes a context-serving layer between project tracing and AI maintenance.
- Roadmap now marks v0.2 context-serving pieces complete.

### Safety

- Generated private context indexes are gitignored by default.
- The indexer excludes common secret, cache, binary, generated, and dependency folders/files.
