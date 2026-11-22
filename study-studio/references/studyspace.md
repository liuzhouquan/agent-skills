# Studyspace files

Create and maintain this structure in the resolved studyspace, not in the skill package:

```text
<topic>-studyspace/
  goal.md
  assets.json
  note/
    README.md
    <question-slug>.md
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

## Current position
- Current question / goal ID:
- What is established:
- Open questions:
- Next action:
- Last updated:
```

Use `pending`, `in_progress`, `completed`, and `needs_review` for goals. Add checkboxes for an at-a-glance view if useful, but keep evidence and achieved level explicit. The hierarchy is flexible; do not invent child goals simply to fill the template.

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
      "path": "resources/retry.pdf",
      "sha256": "<observed hash>"
    }
  ]
}
```

Use absolute canonical paths for external resources and studyspace-relative paths for internal resources. Types include `code`, `pdf`, `markdown`, `text`, and `other`. Omit unknown metadata instead of inventing it. Resource IDs remain stable when paths move; record revisions supporting a claim in the note so an updated registry does not erase historical provenance. For non-Git code directories, record known version information and hashes of studied files where useful. Add `last_checked` or availability information when actually checked. Validate JSON after editing.

## note/README.md

Maintain links to question notes with goal IDs, resource IDs, a short conclusion, and status (`open`, `resolved`, or `needs_review`). Keep it navigational rather than duplicating full notes.

## Question note

```markdown
# <Question title>

- ID: Q1
- Goals: G1.1
- Resources: R1, R2
- Status: open
- Updated: <date>

## Question and intent
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
