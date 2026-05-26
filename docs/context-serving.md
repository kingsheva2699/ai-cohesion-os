# Context Serving Layer

AI Cohesion OS v0.2 adds a small context-serving layer: a local index that breaks workspace files into bounded, source-linked chunks.

The goal is simple:

> Stop loading whole folders into an AI chat. Serve the smallest relevant slice of context, with path and line numbers.

## Why this matters

AI-heavy work breaks down when context is scattered or oversized:

- agents reread too much;
- chats become bloated;
- important files are missed;
- private/generated artifacts get mixed into useful context;
- different tools form different pictures of the project.

A context-serving layer gives every AI tool the same retrieval habit:

1. route to the right project/file;
2. search small chunks;
3. load exact line-bounded excerpts;
4. preserve source paths so claims can be checked.

## What gets built

Running the context indexer creates a local `.cohesion/` folder inside your workspace:

```text
my-ai-workspace/
  .cohesion/
    context_index.json
    context_chunks.json
```

- `context_index.json` stores file-level metadata: path, title, headings, size, hash, and snippet.
- `context_chunks.json` stores smaller retrieval chunks: path, line range, heading, text, and snippet.

Generated `.cohesion/` files are local operational artifacts. Do not commit private workspace indexes unless you intentionally want to publish that workspace map.

## Commands

From the AI Cohesion OS repo:

```bash
python scripts/init_workspace.py ./my-ai-workspace
python scripts/context_index.py ./my-ai-workspace build
python scripts/context_index.py ./my-ai-workspace query "open loops" --top 5
python scripts/context_index.py ./my-ai-workspace get projects/example_project/project_profile.md --lines 80
```

## Retrieval discipline

Good AI context use should follow this order:

1. **Route first** - identify the relevant project/domain.
2. **Chunk search second** - find the best small section.
3. **Exact excerpt third** - load the path and line range needed for the task.
4. **Whole file last** - only when the file itself is the object being edited or reviewed.

This keeps the assistant from wasting tokens on old logs, generated exports, duplicate files, or unrelated project history.

## Safety defaults

The starter indexer excludes common high-risk/noisy artifacts:

- `.git/`, virtual environments, `node_modules/`, caches;
- `.env`, key/certificate/credential-looking files;
- databases, logs, zips, PDFs, XLSX files, images;
- generated index files themselves.

These defaults are conservative, not complete security. If your workspace contains sensitive data, keep the index local and review exclusion rules before sharing.

## How this connects to project tracing

Project tracing answers: "What is true about this work right now?"

Context serving answers: "What exact slice of source-backed context should the AI load to act on that truth?"

Together they create AI cohesion:

- project profiles define current state;
- decision logs preserve why choices were made;
- context chunks make the right source material cheaply retrievable;
- reports and agents can work from the same grounded project reality.
