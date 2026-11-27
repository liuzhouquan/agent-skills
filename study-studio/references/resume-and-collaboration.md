# Multiple studyspaces and session recovery

## Private locator registry

Keep the registry at `${STUDY_STUDIO_HOME:-~/.local/share/study-studio}/index.json`, outside the skill package. In shell commands expand the actual home directory; do not treat a literal tilde in JSON as an absolute path. Use a private directory (0700 where supported) and file permissions (0600). Never publish it or copy its entries into skill examples.

The JSON shape is `{"schema_version": 1, "studyspaces": [...]}`. Each entry has a stable `id`, `title`, `aliases` array, absolute canonical `path`, brief `description`, `status`, and `updated_at`. Paths and personal titles are private data. Register a newly created or explicitly selected studyspace; merge entries without discarding other projects. If the directory moves, verify its identity before updating its path.

Resolve in this order: explicit user path; current studyspace/nearest parent with its local entry instructions and state; exact registry ID or alias; title/description matches. An explicit request for a different named project takes precedence over the current directory. If several matches fit, show minimal names and paths and ask which one. If no index exists, check the user-supplied path or ask for it; do not scan unrelated private directories or reconstruct history from memory. Tell the user which studyspace was selected.

## Required local entry and state

Create `AGENTS.md` in each studyspace with these instructions: use Study Studio when available, read `state.md`, `goal.md`, `plan.md`, `assets.json`, relevant `draft.md` topics, and `note/README.md`, follow relevant notes/session references, verify current source identity, save learning state, and keep personal records local. Include the same recovery steps so another agent can proceed even without the skill installed.

`state.md` contains:

- stable studyspace ID and topic;
- last update and local revision number;
- current goal ID/question and lifecycle status;
- established conclusions with note/evidence links;
- unresolved questions and missing inputs;
- a concrete next action;
- last session record link;
- optional verification checkpoint: round status/scope, original learning position, evaluated questions, pending question, draft evidence link and gaps; resume questioning only on request;
- active work claims: agent/session ID, task scope, files owned, start/update time, and status.

Initialize unknown details explicitly as unknown. A newly created workspace has no source evidence, no achieved mastery, and no learning history until real study occurs. Do not assume that a similarly named repository is the source.

After meaningful work, add `sessions/<date>-<unique-session-id>.md` with the question, agent/session identifier, changes, evidence/commands actually observed, remaining gaps, and next action. Update `state.md` to point to it. This is a compact handoff, not a raw transcript. Keep goals/mastery in `goal.md`, learning sequence and resource ranges in `plan.md`, questions/preliminary answers in `draft.md`, agreed topic syntheses in `note/`, and source paths in `assets.json`; state links to those records rather than duplicating them.

On resume, read the current state and last session record, then the linked goals, resource metadata, and relevant notes. Verify sources supporting the next action. Briefly state where study stopped and what comes next. Missing or conflicting state is an explicit gap, not permission to invent completed work.

## Multiple agents

Sequential handoff works from shared files without access to the previous chat. Before editing shared records, reread them and claim a bounded task with a unique session/agent ID. Independent agents can prepare separate temporary outputs; the coordinator merges related questions into `draft.md`. Use distinct session filenames where necessary, and create formal topic notes only under the consolidation workflow. One coordinator merges shared goal, state, index, and registry updates. Recheck file contents before saving; if they changed, merge or coordinate rather than overwriting another agent's work. Increment the state revision on each shared update.

Work claims are advisory, not a locking implementation. True simultaneous writers must use a filesystem lock for read-modify-write operations or an agreed single writer. Write JSON to a temporary file in the same directory and atomically replace it under that coordination; atomic replacement alone does not prevent lost updates. Do not steal a claim merely because it looks old: confirm the owner has stopped or ask before reassignment.

## Privacy

Private by default: keep studyspace contents, registry, extracted documents, source paths, background, and session history out of the public skill repository. Create a studyspace `.gitignore` with `*` unless the user explicitly chooses versioning/sharing. Explain that ignore rules do not protect already tracked files; check Git tracking before claiming protection and flag tracked private files rather than silently removing history. Do not initialize Git, stage, commit, or push personal study records without explicit authorization. Use only synthetic examples in distributable skill files.
