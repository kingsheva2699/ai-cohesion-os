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

## What this is

A downloadable local-first starter kit for building a personal/team AI operating layer:

- durable project memory
- decision logs
- open-loop tracking
- weekly reports
- useful-data scoring
- stale-context detection
- source-backed project profiles
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
  templates/
    project_profile.md
    weekly_report.md
```

The weekly report script writes a report under `reports/` showing discovered projects and missing profiles.

## Philosophy

1. **AI tools are only as useful as the context layer they share.**
2. **Project tracing is the means; AI cohesion is the result.**
3. **Cohesion beats more tools.**
4. **Do not remember everything. Remember what changes decisions.**
5. **Management/tracking should emerge from the operating layer.**
6. **AI drafts and recommends; humans approve external actions.**
7. **Local-first by default. Private work stays private.**

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

Early starter-kit version. The first goal is practical usefulness: let people download it and immediately make their AI/project setup more coherent.

## License

Apache-2.0.
