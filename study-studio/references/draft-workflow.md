# Questions, ideas, and possible learning changes

`draft.md` is a working notebook, not an implementation queue. Capture ideas without requiring the learner to decide immediately. Group by stable topic IDs; within a topic use QA and suggestions/change sections. Keep the user's original intention separate from the assistant's evaluation. Routine logistics do not need entries.

## Mark items at capture time

Use topic-level defaults for simple QA; add item-level fields when an idea could change the study. Unknown fields stay `undecided`; do not invent urgency or require a lengthy form for every question.

- **Kind:** QA, suggestion, or proposed change (a topic may contain all three).
- **Maturity:** `exploring`, `ready_to_propose`, or `consolidated`. Mark unanswered or unverified parts separately.
- **Disposition:** `unconfirmed`, `proposed`, `accepted`, `deferred`, `rejected`, or `applied`. A user's question is not acceptance of the assistant's recommendation.
- **Plan impact:** one of the four routes below, `none`, or `undecided`; give a brief reason and affected goal/unit.
- **Triggers:** separately state when to propose a formal note, when to revisit a plan change, and what must be settled before applying it. Include concrete destination files/sections and dependencies when known. An immature idea may simply wait for more examples or a learner decision.

## Four routes for changes

| Route | When it fits | Handling |
| --- | --- | --- |
| `replan_now` | New evidence invalidates goals, prerequisites, or the current route | Surface promptly; identify affected goal/plan/README/state and propose a coordinated revision. Immediate evaluation does not mean automatic adoption. |
| `insert_step` | A bounded addition naturally fits an existing unit | Name the unit, precise reading/activity and completion evidence. Incorporate when authorized and ready, normally before that unit. |
| `after_plan` | Useful extension that is not needed for present goals | Keep a deferred item with a review trigger at track review or after the core route; do not silently extend current scope. |
| `new_unit` | Important subject requires its own objective, prerequisites and substantial study | Propose a separate unit and its insertion point, duration and completion evidence; check dependencies before changing the route. |

Importance and urgency differ. A useful topic can be deferred; an interesting tool name does not justify redesigning the plan. Distinguish a short comparison activity from full implementation: they may belong to different routes.

## Consolidation and application are independent

A mature explanation may warrant a formal note without changing the plan. A narrow, well-supported learning step can be proposed for the plan before there is enough material for a full topic note. Evaluate both explicitly; avoid treating either as implementation or learner mastery.

When asked to evaluate only, record a recommendation as `proposed`, leaving the authoritative plan unchanged. When the user explicitly requests the actual change, apply it within that scope without asking again. For tentative ideas, unresolved architecture choices, or major revisions beyond the request, first show the concrete proposed change and obtain the missing decision. Avoid repeatedly asking about the same pending item.

After an authorized change, record what changed, why, and links to the destination in the draft; mark `applied` and update dependent plan/README/state or goals as necessary. Preserve useful questions and rejected/deferred alternatives without keeping duplicate full syntheses. Formal note creation follows the same explicit request or agreement rule.

## Compact topic template

```markdown
<a id="t1"></a>
## T1 — <Topic>
- Goals / units / resources:
- Maturity: exploring
- Updated:

### QA
- Q1: <Question, including intent>
- Current answer and source locators:
- Follow-ups / uncertainty:

### Suggestions and possible changes
#### I1 — <Idea>
- User intent / assistant assessment:
- Disposition: unconfirmed
- Plan impact: undecided — <reason; candidate destination>
- Revisit trigger:
- Apply prerequisites / authorization:
- Proposed reading/activity and completion evidence:

### Formal note trigger
<What scope/evidence would make a reusable topic note worthwhile; pending agreement or link to agreed note.>
```

Read the topic index and relevant sections on resume. Consolidate related entries in place. If the file becomes unwieldy, propose an indexed archive of settled topics; do not revert to one file per question. Shared draft writes require the same coordination as state and plan updates.
