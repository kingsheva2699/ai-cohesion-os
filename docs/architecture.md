# Architecture

## Layers

1. **Workspace structure**
   - `/projects`
   - `/inbox`
   - `/reports`
   - `/memory`
   - `/templates`
   - `/systems`
   - `/connectors`
   - `/tools`

2. **Project profiles**
   - status
   - owner
   - sources
   - decisions
   - open loops
   - risks
   - next actions

3. **Data-value scoring**
   - actionability
   - decision impact
   - durability
   - confidence
   - project relevance
   - risk reduction
   - leverage/reusability

4. **Context serving layer**
   - file-level metadata index
   - small section/line chunks
   - path and line references
   - bounded excerpts for AI tools
   - conservative local exclusions for secrets, caches, generated artifacts, and binary files

5. **Connector health layer**
   - local system export checks
   - optional HTTP probes
   - freshness windows
   - machine-readable and human-readable health reports

6. **Tool module layer**
   - public-safe module registry
   - README / MANIFEST / PRIVACY / VALIDATION scaffolds
   - GitHub readiness checks before publishing reusable tools

7. **Context guidance layer**
   - broad raw indexes for files, chat exports, logs, and source manifests
   - task-specific retrieval before deeper AI analysis
   - source-backed extraction of decisions, open loops, facts, and stale claims
   - selective promotion into durable memory/project files

8. **Maintenance scripts**
   - initialize workspace
   - build context indexes
   - scan project files
   - generate weekly report
   - detect stale projects

9. **Optional AI layer**
   - summarize project changes
   - draft reports
   - classify open loops
   - suggest next actions

10. **Future UI**
   - visual project orbit
   - health dashboard
   - source-linked graph

## Local-first principle

The first version should work entirely as files and scripts. This reduces privacy concerns and makes adoption easier.
