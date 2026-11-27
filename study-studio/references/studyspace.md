# Studyspace files

Create and maintain this structure in the resolved studyspace, not in the skill package:

```text
<topic>-studyspace/
  README.md                  # learner entry point and resource links
  plan.md                    # learning route, units and reading ranges
  AGENTS.md                  # local entry instructions for any agent
  state.md                   # authoritative current position and work claims
  sessions/                  # concise dated handoff records
  .gitignore                 # private by default
  goal.md
  assets.json
  draft.md                      # questions, tentative ideas and proposed changes
  note/
    README.md
    <topic-slug>.md
  derived/                   # optional; generated text extracts, including PDF Markdown
  resources/                 # optional; only when storing actual resources
```

## goal.md

```markdown
# <Topic>

## Purpose and learner context
- Intended outcome:
- Background and constraints (user supplied):
- Scope and deferred topics:

## Goals
### G1 — <Goal>
- Target level: 2 — can explain
- Status: pending
- Achieved level: not assessed
- Evidence and notes:
- Remaining gap:

#### G1.1 — <Smaller objective>
- Target level:
- Status: pending
- Achieved level: not assessed
- Evidence and notes:
- Remaining gap:

## Progress
See `state.md` for the current question, next action, and session handoff.
```

Use `pending`, `in_progress`, `completed`, and `needs_review` for goals. Add checkboxes for an at-a-glance view if useful, but keep evidence and achieved level explicit. The hierarchy is flexible; do not invent child goals simply to fill the template.

## README.md and plan.md

The learner entry page links original resources, searchable derivatives, goals, the roadmap, state, and note index. Point to one concrete starting unit rather than a list of unrelated resources.

`plan.md` contains an ordered, adjustable route. Each unit has a stable ID, linked goal IDs, status, a mechanism-level question, exact reading links and ranges (PDF pages, Markdown headings, source symbols), an activity, estimated duration, and completion evidence. Keep at most one unit in progress; do not mark a unit started or mastered simply because the assistant prepared materials. Teach or guide reading before requiring a learner explanation. Link completed units to evidence rather than duplicating goal mastery records. State tracks the current position; the plan supplies the next unit's details.

## assets.json

A small registry, not a copied corpus. Example shape (replace illustrative values with actual observations):

```json
{
  "schema_version": 1,
  "topic": "retry design",
  "primary_resource_id": "R1",
  "resources": [
    {
      "id": "R1",
      "type": "code",
      "title": "service",
      "description": "Service repository containing the request retry implementation under study.",
      "path": "/work/service",
      "git": {
        "remote": "https://github.com/example/service.git",
        "branch": "main",
        "commit": "<observed commit>"
      }
    },
    {
      "id": "R2",
      "type": "pdf",
      "title": "retry paper",
      "description": "Paper describing retry strategies and backoff tradeoffs.",
      "path": "resources/retry.pdf",
      "extracted_text": {
        "path": "derived/pdf-text/R2.md",
        "format": "markdown",
        "tool": "pdftotext",
        "source_sha256": "<observed hash>"
      },
      "sha256": "<observed hash>"
    }
  ]
}
```

Every resource entry must have a concise `description` explaining what it contains and why it is relevant to this study. Base it on the file contents, repository documentation, or the user's explanation. If its role is not yet known, use a transparent placeholder such as `"description": "Purpose not yet established; inspect before relying on it."` and revisit it when the resource is inspected. Do not infer a resource's contents from its filename alone. `extracted_text` is optional and records a generated derivative; preserve the original `path` as the authoritative source.

Use absolute canonical paths for external resources and studyspace-relative paths for internal resources. Types include `code`, `pdf`, `markdown`, `text`, and `other`. Omit unknown metadata instead of inventing it. Resource IDs remain stable when paths move; record revisions supporting a claim in the note so an updated registry does not erase historical provenance. For non-Git code directories, record known version information and hashes of studied files where useful. Add `last_checked` or availability information when actually checked. Validate JSON after editing.

## draft.md

Maintain one topic-based draft with an index and stable anchors. Each topic separates QA (questions, preliminary answers, evidence, unresolved follow-ups) from suggestions and possible changes. Use [draft-workflow.md](draft-workflow.md) for the compact topic/item template, maturity, four impact categories, and explicit triggers for consolidation or action. Preserve existing content and stable topic IDs when migrating from an older `qa.md`; update active links rather than keeping duplicate full copies.

## note/README.md

Maintain links to agreed, consolidated topic notes with goal IDs, resource IDs, a short conclusion, and status (`open`, `resolved`, or `needs_review`). Keep it navigational rather than duplicating full notes.

## Consolidated topic note

```markdown
# <Topic title>

- Topic ID: T1
- Source questions: draft.md#t1
- Goals: G1.1
- Resources: R1, R2
- Status: open
- Updated: <date>

## Questions and intent
<Preserve what the learner asked and the intended application.>

## Reusable conclusion
<Direct answer; mark provisional conclusions explicitly.>

## Explanation and evidence
<Source trace or reasoning. Cite resource ID, file/symbol or page/heading,
revision/hash as appropriate. Separate fact, observation, and inference.>

## Application and boundaries
<When the conclusion applies; adaptations, assumptions, or tradeoffs.>

## Experiments
<Only if relevant: command or exercise, environment, actual result,
and reproducible steps. Label unrun proposals.>

## Open questions and next action
<Unresolved parts; follow-up note links when relevant.>
```

Omit empty optional sections. Record meaningful corrections with their reason; avoid producing a new note for each follow-up message. Goal completion and note resolution are separate states.

## Recovery and coordination

Use [resume-and-collaboration.md](resume-and-collaboration.md) for state, session records, private registry, and shared-write conventions. `goal.md` owns target hierarchy and mastery; `plan.md` owns sequence and study materials; `state.md` owns the current position. Avoid maintaining competing current-position sections.

## Verification rounds

For requested interview-style checks, follow [verification-mode.md](verification-mode.md). Store grouped question/answer evidence and recommendation-first debriefs under a unit topic in `draft.md`; `state.md` holds the round checkpoint and original learning position. No separate per-question files or prepopulated learner results.
