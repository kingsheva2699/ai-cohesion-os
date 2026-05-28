# Roadmap

## v0.1 - Starter kit

- [x] Local workspace initializer
- [x] Project profile template
- [x] Decision log template
- [x] Weekly report template
- [x] Basic weekly report script
- [x] Data-value scoring docs
- [x] Privacy model

## v0.2 - Context serving + project tracing scanner

- [x] Create local `.cohesion/` workspace system folder
- [x] Build file metadata index JSON
- [x] Split source files into bounded context chunks
- [x] Add chunk query CLI
- [x] Add bounded excerpt CLI
- [x] Document context-serving retrieval discipline
- [ ] Detect stale projects by last update
- [ ] Extract open loops from Markdown checklists into structured project index
- [ ] Add `cohesion status` CLI wrapper

## v0.3 - Connector health + protocol readiness

- [x] Add `systems/` export folder
- [x] Add `connectors/connectors.json` configuration
- [x] Add connector health CLI
- [x] Check required paths, freshness, and optional HTTP probes
- [x] Write machine-readable and human-readable health reports
- [x] Wire connector health into smoke tests
- [ ] Add connector-specific normalization recipes
- [ ] Add watch/sync examples for cron, Zapier, Make, and local scripts

## v0.4 - AI-assisted maintenance

- [ ] Optional LLM summarizer interface
- [ ] Source-backed weekly report drafts
- [ ] Decision/open-loop extraction prompts
- [ ] Human approval gate pattern

## v0.5 - Project Orbit UI

- [ ] Static graph from project index
- [ ] Project freshness/status colors
- [ ] Dependency links
- [ ] Local browser dashboard

## v0.6 - Live integration adapters

- [ ] GitHub issues/PR summaries
- [ ] Notion/Markdown export ingest
- [ ] Slack/Discord/Telegram export ingest
- [ ] Linear/Jira/ClickUp import adapters
- [ ] OAuth/API connector examples
- [ ] Retry queues and connector health probes for live adapters

## v1.0 - Local-first AI cohesion layer

- [ ] Stable CLI
- [ ] Stable schemas
- [ ] Docs and examples
- [ ] Privacy/safety defaults
- [ ] Repeatable install flow
