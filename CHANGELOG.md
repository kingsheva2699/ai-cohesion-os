# Changelog

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
