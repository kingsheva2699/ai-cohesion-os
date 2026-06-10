# Context Guidance Layer

AI Cohesion OS should not make agents remember everything.

It should help them decide what to look at, when to look at it, and what is safe to promote into durable memory.

## Core principle

> Index broadly, reason narrowly, promote selectively.

That means:

1. Keep raw sources preserved and searchable.
2. Use general indexes to find candidate context.
3. Run deeper AI/subagent analysis only on the relevant slices.
4. Promote only source-backed, decision-changing information.

This avoids turning noisy chat logs, stale brainstorms, generated exports, or partial tool output into false long-term memory.

## Why not summarize everything?

Blindly running every historical input through a model creates problems:

- exploratory ideas can be mistaken for decisions;
- stale project state can become false authority;
- private/customer context can leak into public or shared outputs;
- duplicate/generated logs can overwhelm useful signal;
- model summaries can hide the original source and uncertainty.

Raw logs are evidence. Model summaries are interpretations.

AI Cohesion OS should preserve evidence first, then interpret only when a task requires it.

## Retrieval flow

Good context use follows this order:

1. **Route** — identify the relevant project, domain, person, system, or source type.
2. **Search** — use file/chat/session indexes to find candidate slices.
3. **Extract** — load bounded source-linked excerpts, not whole archives.
4. **Reason** — use an AI/subagent pass on the narrowed slice.
5. **Promote** — save only durable, useful, source-backed conclusions.

## What a subagent/model pass should extract

When deeper analysis is needed, ask for typed outputs:

- decisions;
- durable project facts;
- open loops;
- user/team preferences;
- risks or blockers;
- stale or superseded claims;
- contradictions;
- source paths and timestamps.

Every extracted item should keep provenance:

- source file or session;
- line/message range when available;
- timestamp;
- confidence;
- freshness notes.

## Promotion rules

Promote extracted context only when it changes future action.

Good promotion targets:

- project profile / README;
- decision log;
- open-loop tracker;
- user/team preference file;
- reusable workflow/skill doc;
- public-safe tool module documentation.

Do not promote:

- one-off task progress;
- stale brainstorm fragments;
- secrets or credentials;
- private customer records;
- raw chat dumps;
- model guesses without source backing.

## Relation to context serving

Context serving answers:

> What exact source slice should the AI load?

Context guidance answers:

> Which source type should the AI consult at all, and what should happen to what it finds?

Together:

- context indexes make sources retrievable;
- guidance rules prevent overloading the prompt;
- subagent/model passes interpret only narrowed evidence;
- promotion rules keep durable memory clean.

## Public-safe boundary

The starter kit should provide the pattern, schemas, and scripts.

Private workspaces decide which sources are indexed and which extracted facts are promoted.

Generated indexes and extracted private summaries should stay local unless intentionally reviewed and published.
