# Learning Artifacts

Create only the files that help the learner's chosen scope. For an ongoing track, keep notes outside the source checkout by default. Use `~/source-code-learning/index.md` to locate tracks and keep one `state.md` per track; update it as learning progresses.

## Track index (`~/source-code-learning/index.md`)

```markdown
# Source Code Learning Tracks

| Track | Source path | State file | Current goal | Updated |
| --- | --- | --- | --- | --- |
| <name> | <canonical path> | <absolute path>/state.md | <mechanism> | <date> |
```

Add or update one row per track. Use distinct names when source directories have the same basename. Avoid putting credentials or private source excerpts in the index.

## Project overview

```markdown
# <Project> — Source Code Learning

## Learning goals
- Mechanism:
- Target mastery: purpose | explain implementation | modify and reproduce
- Why this matters:

## Source identity
- Source path:
- Remote:
- Branch:
- Commit:
- Other revision / studied file content hashes (when no Git metadata):
- Runtime/tooling:

## Knowledge map
- Mechanism and prerequisites:
- Dependencies / adjacent mechanisms:
- In scope:
- Deferred:

## Code map
- Entry point:
- Relevant files and symbols:
- Call/data/control flow:
- Tests and configuration:

## Completion evidence

## Current status and next action
- State file:

## Open questions

## Transfer candidates
```

## Learning plan

```markdown
# Learning plan

## L01 — <mechanism>
- Status: pending | in_progress | completed | needs_review
- Objective:
- Target mastery:
- Source range (files and symbols):
- Prediction or practice:
- Core questions:
- Completion evidence:
- Estimated time:
- Next action:
```

Keep only one unit `in_progress`. Do not mark a unit complete without evidence for its target level.

## Persistent session state

```markdown
# Source Code Learning State

## Identity
- Workspace / overview path:
- Source path:
- Remote:
- Branch:
- Commit:
- Other revision / studied file content hashes (when no Git metadata):
- Last verified:

## Current goal
- Mechanism:
- Target mastery:
- Current unit and status:
- Exact stopping point:

## Mastery and evidence
- Current level:
- Learner explanation or artifact:
- Source paths, symbols, call chain:
- Experiment / command and result:
- Reproduction steps (required for level 3):
- Remaining gap:

## Decisions and changes
- Scope or plan changes and reason:
- Source drift checked:

## Transfer value
- Candidate implementation:
- When it applies:
- Adaptations / tradeoffs:

## Next session
- Read these files / symbols:
- Do this next:
- Questions to resolve:
```

## Unit record

```markdown
# <Date> — <mechanism / unit>

## Objective and target mastery

## Source trace
- `path/to/file` — `symbol`: role in the path
- Call/data/control chain:

## Prediction and practice

## Result and reproducible steps

## My explanation

## Achieved level and evidence

## Transfer value and tradeoffs

## Remaining gap / next action
```

## Concept note

```markdown
# <Mechanism>

> Purpose:

## When it is used

## Implementation trace
- Entry point:
- Files and symbols:
- Call/data/control flow:

## Evidence
- Source facts:
- Experiment and result:
- Inferences / uncertainty:

## Mastery
- Level:
- What I can explain or reproduce:
- Remaining gap:

## Transfer to my project
- Reusable idea:
- Applies when:
- Adaptations and tradeoffs:

## Questions I should answer without notes
-
-
```
