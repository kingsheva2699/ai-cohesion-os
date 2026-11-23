# Resume a project without reconstructing the last chat

`python scripts/resume.py <project-directory>` displays a source-reviewed handoff, not a command to perform the task. A new assistant on the same machine can run it, or you can give another tool the resulting text. `--json` returns the same cited fields. No plugin, index rebuild, API key or model is needed for discovery, review, or replay.

## Try the process without using personal data

From the repository root, run `python scripts/demo_handoff.py`. The only projects, notes, proof records and profile storage it uses are created in a temporary directory. No model, server, registry or sign-in is needed. For a graphical view of **your own explicitly enrolled projects**, run `python scripts/pickup_view.py` (requires Tk). Copy rechecks the selection; a handoff on hold is not copied. `pickup.py list` and `pickup.py show --id ID` also work without Tk. This repository ships a generic picker, not a personal dashboard or a populated registry.

## First use: discover, check, record

```sh
python scripts/resume.py ./my-project --topic "returns pilot" --discover
```

This searches eligible notes under the actual directory, including archives and proposals, and shows candidate lines, warning candidates and the inventory digest. **A ranking is not an approval.** Read the surrounding files. Verify who decided, applicability, conflicts, dependencies and any missing replacement. If an operative source lives outside the declared scope, do not review an actionable handoff until the source is covered. The `--topic` is part of the cache key; use the same topic or consistently omit it.

For a Project Orbit directory or a registered subproject document, add `--registry <local-projects.json> --project <exact-ID-or-alias>` to every command. Root is an explicit permission boundary, not an automatically followed registry path. Duplicate or partial names do not select a project. The `orbit:<id>/nextAction` reference denotes that exact field on the matching ID, not a Markdown line. It is the **recorded** next step, not proof that it has not already been done. Check it against the project notes. If the selected row names related text documents outside the project, explicitly allow those individual files with repeated `--include-note <absolute-file>`; don't widen the project to a home directory. Missing/uncovered registered note dependencies block a reviewed handoff. Registry changes affecting the selected row are checked on each invocation.

After inspecting the underlying evidence, save references (replace every example value with the discovery result):

```sh
python scripts/resume.py ./my-project --topic "returns pilot" --review DIGEST --reviewer "source review" --rule 'decisions.md#L8' --next 'tasks.md#L12'
python scripts/resume.py ./my-project --topic "returns pilot"
```

`--rule`, `--next` and supporting `--cite` can be repeated. For a conflict, use **only** a blocking question with the competing sources, for example `--question 'Which location is in force?' --cite 'one.md#L2' --cite 'two.md#L3'`. A clarification shows the question and references, not a proposed action. Review identifies the person or assistant that checked the sources; it does not signify owner approval. No project action is ever executed. A model or script may consume `mode: resume`; it must **not** treat `discovery`, `hold`, `clarify`, or any `draft-*` as actionable. A hold exits with status 2.

## Prove a finished step and leave the review open

For a task that generates a local JSON artifact, capture the expected inputs and checks **before** it runs. Have the reviewed card cite both the generation instruction and the subsequent review instruction (`--cite` can name the latter). Write a local proof specification; for example:

```json
{"output":"report.json","inputs":["records.csv"],"checks":{"/status":"ready","/rowCount":4},"next_source":"tasks.md#L8","next_text":"Review the resulting report."}
```

Run `python scripts/resume.py ./my-project --topic "returns pilot" --begin SPEC.json`, then generate the artifact through the normal, separately authorized process. Run the same command with `--finish` instead of `--begin SPEC.json`. A new session verifies the input hashes, output checks and saved artifact hash before showing the cited review as next. An interrupted attempt, missing artifact, changed inputs or invalid output leaves a hold, not an invitation to repeat the action. Choose checks that identify the right output; this is not proof of subjective quality or who wrote it. `@registry` can bind the exact registry used in registry-scoped mode. Never substitute a filename or a model's assertion for evidence. The output directory must exist, the target file must not already exist at `--begin`, and at least one local input and one content check must be declared.

A stale handoff lists added, modified and removed source names, and tells you which cited references still match. It does not treat an uncited note as harmless. First-generation cards need a new review to acquire file-level fingerprints. Re-review of unchanged substantive citations preserves completion evidence; an intentionally superseded task can be retired with `--replace-task` on an explicit review. Replaced completion records are archived outside the project. `--waiting-on-you` on a reviewed handoff explicitly marks a human dependency; outstanding review alone does not assign it to the owner.

## Pick up where I left off

Opt in only the projects you want on the local pickup board. The registry adapter is optional. Enrollment can be reversed; it does not change Project Orbit's registry or expose the workspace to another AI. After first review, run `python scripts/pickup.py add --id returns --label "Returns pilot" --root ./my-project --topic "returns pilot"`. For registry projects include the same `--registry`, `--project` and `--include-note` arguments used to review them. `python scripts/pickup.py list` gives compact project summaries; `python scripts/pickup.py show --id returns` revalidates and returns only the selected handoff; `python scripts/pickup.py remove --id returns` opts out without deleting the reviewed card. The list and details are for the local operator; share only the selected handoff. Reading a handoff never executes or authorizes a project action.

## Optional local writer

`--draft` instead of `--discover` asks an already installed `qwen2.5-coder:7b` at `127.0.0.1:11434` to suggest references. The request uses a fixed loopback URL with proxies and redirects disabled. No downloads or remote fallback. An unavailable writer, invalid output, or unresolved evidence is not converted into a reviewed handoff. The writer never saves a card. Skip it entirely for sensitive notes or when you want deterministic behavior.

## Scope and storage

- Reads UTF-8 `.md`, `.txt`, `.rst` and `.adoc` notes. Skips hidden, dependency, fixture, template, test, example, build, export and secret-like paths and linked entries. It does not scan email, chats, source code, cloud drives on purpose, or arbitrary registry links. Point it only at material suitable for the intended recipient; filename filters are **not** content redaction. Do not put state on a network/synced disk if the source is private.
- Ordinary discovery/serve do not write state. `--review`, `--begin` and `--finish` write local per-user handoff state outside the source tree (`--state-dir` or `COHESION_RESUME_STATE` can override). State includes cited text; treat it as private and trusted. It is not a tamper-proof audit log. Project notes and the registry are never edited.
- Each replay rereads the eligible inventory, hashes all bytes and checks the cited lines or registry field. A new, edited or removed eligible note invalidates the card, even if its previous quotes still match. An unrelated note edit may therefore require re-review. Binary sources, repositories in other locations, decisions not written down, and concurrent changes after display are outside the guarantee. A pasted card is a snapshot; rerun before relying on it later.
- This is an opt-in local CLI, not an installed agent hook or a change to live operating defaults. It is designed for ordinary trusted local files, not for a filesystem or state store actively controlled by an adversary.
