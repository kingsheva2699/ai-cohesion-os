# AI Cohesion OS

A local-first starter kit for making your AI tools, project files, memory, agents, models, and workflows behave like one coherent operating system.

Most people using AI have the same problem: the tools are powerful, but disconnected.

- Chat history lives in one place.
- Project files live somewhere else.
- Decisions disappear.
- AI agents forget context.
- Local models, frontier models, scripts, notes, and automations do not share a durable operating layer.
- Project management becomes manual cleanup after the fact.

**AI Cohesion OS fixes the layer underneath.**

It gives your workspace a self-maintaining memory and management structure so AI can coordinate around durable context instead of starting from scratch every time.

## Core promise

> Make your AI setup cohesive enough that project tracking, memory, reporting, and execution visibility become side effects.

## Mechanism

The mechanism is **project tracing**: continuously maintaining source-backed project profiles, decisions, open loops, stale checks, useful-data scoring, and reports so AI tools can share the same operational reality.

v0.2 adds **context serving**: chunking the workspace into small path-linked sections so AI tools can load only the context they need. See [`docs/context-serving.md`](docs/context-serving.md).

v0.3 adds **connector health**: a local-first health gate for customer-system exports and optional probes so AI tools know whether email, CRM, calendar, chat, and webhook context is present and fresh before relying on it. See [`docs/connector-health.md`](docs/connector-health.md).

v0.4 adds **tool modules**: a public-safe registry and scaffolding pattern for turning internal workflow modules into GitHub-ready tools with README, manifest, privacy boundary, and validation files. See [`docs/tool-modules.md`](docs/tool-modules.md).

v0.5 drafts **context guidance**: the discipline of indexing broadly, reasoning narrowly, and promoting selectively so AI tools can retrieve the right source-backed slice without turning every old input into long-term memory. See [`docs/context-guidance.md`](docs/context-guidance.md).

## What this is

A downloadable local-first starter kit for building a personal/team AI operating layer:

- durable project memory
- decision logs
- open-loop tracking
- weekly reports
- useful-data scoring
- stale-context detection
- source-backed project profiles
- bounded context chunks for efficient AI retrieval
- local context indexes with path/line references
- connector health checks for customer-system exports/probes
- public-safe tool module registry and scaffolds
- context guidance for deciding which sources to retrieve, analyze, and promote
- approval gates for external actions
- templates/scripts that any AI assistant can use

It is not trying to replace Jira, Notion, Linear, Asana, ClickUp, Claude, ChatGPT, Cursor, or local models.

It sits underneath them as the **cohesion layer**.

## Who this is for

- AI-heavy operators
- solo founders
- agency owners
- consultants
- indie hackers
- technical project leads
- people using many AI tools but losing continuity
- teams that want AI help without hallucinated memory or scattered context

## What you get after installing

- A workspace structure your AI assistant can maintain.
- Project profiles that survive across sessions.
- A decision log that stops context rot.
- Weekly reports generated from files, not vibes.
- A scoring model for what information is worth remembering.
- A foundation for adding agents, semantic search, local models, dashboards, or automations later.

## Requirements

- Python 3.10+
- Git optional, but recommended
- No API key required for the starter kit
- AI assistant optional; the first scripts are plain local Python

## Quick start

```bash
git clone https://github.com/YOURNAME/ai-cohesion-os.git
cd ai-cohesion-os
python scripts/init_workspace.py ./my-ai-workspace
python scripts/connector_health.py ./my-ai-workspace init
python scripts/tool_registry.py ./my-ai-workspace init
python scripts/tool_registry.py ./my-ai-workspace scaffold lead-intake-fast-reply
python scripts/tool_registry.py ./my-ai-workspace check
python scripts/context_index.py ./my-ai-workspace build
python scripts/context_index.py ./my-ai-workspace query "open loops" --top 5
python scripts/connector_health.py ./my-ai-workspace check --write
python scripts/weekly_report.py ./my-ai-workspace
```

## Example output

The initializer creates:

```text
my-ai-workspace/
  README.md
  projects/
  inbox/
  reports/
  memory/
    decision_log.md
  systems/
  connectors/
    connectors.json
  tools/
    tool_modules.json
    lead-intake-fast-reply/
      README.md
      MANIFEST.json
      PRIVACY.md
      VALIDATION.md
  templates/
    project_profile.md
    weekly_report.md
    context_manifest.json
  .cohesion/
    context_index.json
    context_chunks.json
```

The context indexer writes `.cohesion/context_index.json` and `.cohesion/context_chunks.json` so AI tools can retrieve small source-linked chunks instead of whole folders.

The connector health checker writes `.cohesion/connector_health.json` and a dated Markdown report under `reports/` so AI tools can see whether linked customer systems are healthy, stale, missing, or disabled.

The tool registry creates public-safe module folders with README, MANIFEST, PRIVACY, and VALIDATION files so useful internal workflow patterns can become GitHub-ready tools without leaking private customer context.

The weekly report script writes a report under `reports/` showing discovered projects and missing profiles.

## Philosophy

1. **AI tools are only as useful as the context layer they share.**
2. **Project tracing is the means; AI cohesion is the result.**
3. **Cohesion beats more tools.**
4. **Do not remember everything. Remember what changes decisions.**
5. **Index broadly, reason narrowly, promote selectively.**
6. **Management/tracking should emerge from the operating layer.**
7. **AI drafts and recommends; humans approve external actions.**
8. **Local-first by default. Private work stays private.**

## Market category

This is not just project management.

It is closer to:

- AI cohesion layer
- AI operations layer
- AI workspace OS
- self-maintaining workspace
- project memory system
- execution intelligence layer

## Status

Early starter-kit version. v0.2 adds a local context-serving layer: file metadata, chunked context retrieval, and bounded source excerpts for AI assistants.

v0.3 adds a connector health layer for testing whether customer-system exports/probes are present and fresh. This validates the local communication protocol, not full live OAuth/API integration yet.

## License

Apache-2.0.

## Built by AI FlowPal

AI Cohesion OS is maintained as a public starter kit by [AI FlowPal](https://aiflowpal.com/) - practical AI workflow systems for customer-facing operations, project memory, and follow-through.

