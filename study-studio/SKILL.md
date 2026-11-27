---
name: study-studio
description: Study code across repositories and PDF, Markdown, or text resources through focused questions, and maintain a persistent studyspace with learning goals, source references, and reusable Q&A notes. Use for ongoing resource-grounded learning, automatic note synthesis, or resuming a study topic.
---

# Study Studio

Help the learner investigate concrete questions and turn the answers into reusable, source-backed notes. A topic may draw on several repositories, PDFs, Markdown documents, and text files. Organize the study around the learner's purpose rather than a tour of every resource.

## Establish or resume a studyspace

- Honor an explicitly chosen notes directory. Otherwise look for a matching existing studyspace beside the primary resource before creating one.
- Default to `<primary-resource-parent>/<primary-resource-name>-studyspace/`. For `/work/project/` use `/work/project-studyspace/`; for `/docs/book.pdf` use `/docs/book-studyspace/`. With several resources, use the user-designated primary resource, or the first resource supplied. Without a local resource, default to `~/study-studio/<topic>-studyspace/`.
- Tell the user the exact resolved studyspace path when creating or first resuming it. Do not require confirmation for this ordinary local note creation. Never overwrite an unrelated directory; use a descriptive distinct topic name when needed.
- When already inside a studyspace, use its `AGENTS.md` and `state.md` first. Read `goal.md`, `plan.md`, `assets.json`, the topic index in `qa.md`, the note index, and only relevant draft sections or notes next. For requests such as “continue learning <topic>”, resolve the topic through the private registry described in [references/resume-and-collaboration.md](references/resume-and-collaboration.md). Ask only if several matches remain ambiguous or the workspace cannot be found. Never invent prior progress.
- Initialize only the small structure in [references/studyspace.md](references/studyspace.md). Resources can stay where they are. Register paths rather than relocating or copying files by default. Use `resources/` for user-provided copies when useful or requested.

## Resume and collaborate

Each studyspace is an independent learning project. Follow [references/resume-and-collaboration.md](references/resume-and-collaboration.md) when creating, resuming, handing off, or coordinating a project. Maintain `state.md` as the authoritative current position and `sessions/` as concise session handoff records. Keep personal paths, aliases, study content, and the workspace registry outside the distributable skill.

## Goals and learning context

Maintain `goal.md` as a hierarchy of goals and smaller questions with stable IDs, a target mastery level, status, achieved level, evidence links, remaining gaps, and next action. Capture relevant learner background, constraints, and intended applications only when supplied by the user; identify tentative assumptions as such. Do not infer personal traits from questions.

Maintain a learner-facing `README.md` as the entry point and `plan.md` as the overall learning route. Link each planned unit to goal IDs, exact resource paths and bounded PDF pages/headings or code symbols, a practical activity, estimated time, status, and completion evidence. Make the next reading step actionable; introduce the material before asking the learner to explain it. `goal.md` owns outcomes and mastery, `plan.md` owns sequence and materials, and `state.md` owns the current position. Keep the route flexible as questions reveal gaps.

Start with the user's current question. For a broad request, briefly inspect the supplied resources and offer a few bounded learning directions. Keep at most one learning unit in progress; other goals can remain pending. A unit should usually fit a focused session rather than require reading an entire project or book.

Use these mastery levels per goal:

1. **Knows its purpose:** learner can explain the problem, use cases, and main inputs and outputs.
2. **Can explain it:** learner can reconstruct the important reasoning or implementation, including key decisions and boundaries, using evidence.
3. **Can apply, modify, or reproduce it:** learner independently completes a meaningful application or change and reproduces the outcome with an appropriate check or artifact.

Separate answer resolution from learner mastery. An assistant explanation or experiment can resolve a question without proving that the learner has mastered it. Award levels from learner explanations, predictions, exercises, or artifacts with supporting evidence. Mark a goal completed only when its target has evidence; preserve partial progress without forcing a quiz after every question.

## Read and explain with evidence

Use local resources as primary evidence and inspect only the paths or passages needed for the question. Read each source using its appropriate tools; the skill does not require an indexing service, vector database, or Khoj installation.

- **Code:** trace entry points, symbols, callers/callees, state changes, and data flow. Cite repository ID, file path, symbol, and useful line numbers. Inspect tests and configuration where they establish behavior. Use small code or concept maps when they clarify the current question.
- **PDF:** follow the PDF tool setup and extraction workflow in [references/pdf-workflow.md](references/pdf-workflow.md). Prefer local extraction to a page-marked Markdown cache, then search and read only passages needed for the question. Keep the original PDF as the authoritative source and cite its page numbers. For diagrams, equations, tables, scans, or unreliable extraction, inspect rendered pages or use OCR as appropriate; distinguish PDF page index from printed page number. Do not pass an entire converted book into context when targeted excerpts answer the question.
- **Markdown/text:** read the relevant sections and cite the resource ID, heading, and useful line numbers. Follow linked resources only as needed.
- **Multiple resources:** identify which source supports each conclusion. Surface conflicting versions or assumptions rather than silently combining incompatible claims.

Record resource identity in `assets.json`: canonical path, type, and a content-based description; for Git sources, sanitized remote, branch, and commit; for documents, available version information and a content hash when used. For extracted resources, also record the derivative path, tool, and source hash so stale extracts can be detected. Never store credentials in resource metadata. On resume, check availability and changes to sources supporting the current question; recheck affected conclusions and mark stale notes `needs_review`. Preserve historical evidence instead of rewriting it as current fact. If a path moved, update it after locating the actual resource.

Answer directly, then explain the smallest useful evidence chain. Distinguish source facts, runtime observations, and inference. Run a focused experiment when needed and feasible; use an isolated scratch area for exercises and avoid treating unrun code as a verified result. A useful loop is `predict -> inspect -> observe -> explain -> apply -> verify`, adapted to the learner's question.

## Capture questions in a shared draft, then propose topic notes

Treat use of this skill as authorization to maintain the selected local studyspace. Automatically capture useful learning questions and preliminary answers in one `qa.md` at the studyspace root. Group similar questions and follow-ups under stable topic headings with anchors and a short topic index. Revise the existing topic rather than appending repeated answers or creating a note for each question. Routine logistics and conversational acknowledgments do not need QA entries.

Each topic preserves the question and intent, a concise current answer, follow-up questions, supporting resource IDs and precise evidence locators, uncertainty, and what remains to investigate. Distinguish source facts, observations, inference, and user statements. Preserve meaningful corrections and label unrun experiments as proposals. Track question resolution separately from topic maturity and learner mastery: an answered question can remain in the draft.

When a topic has a coherent explanation, sufficient supporting evidence and clear applicability/limits, propose consolidating it into a topic-based note in `note/`. Explain the proposed scope and why it is ready. Wait for the user's agreement before creating that formal note, unless they already explicitly requested this consolidation. Do not propose after every answer or use a fixed question count as the trigger. Update an existing formal note when the discussion extends the same topic rather than multiplying files.

After agreed consolidation, preserve a short question summary and link from the draft to the formal note, record any remaining questions, and update `note/README.md`. Move the detailed synthesis rather than maintaining two competing full copies. Never discard unresolved questions, provenance, corrections, or learner contributions. Goal evidence may link to draft sections as well as formal notes; promotion alone does not prove mastery.

On resume, search the draft topic index and read relevant sections selectively. If the draft grows large, propose archiving settled groups with navigable links; do not split it into one file per question. At interruption or a meaningful session boundary, update `state.md` and the handoff record with draft/note links and next actions. Do not create a new session record for every minor question; reuse the current record where appropriate. Briefly report meaningful persistence or consolidation, without forcing a save report after each turn. If saving fails, state the failure rather than claiming persistence.

Keep the skill itself separate from personal study data. Invoking it authorizes local note maintenance, not publishing, committing, or pushing a learner's notes. Respect explicit requests to skip saving or keep particular information out of notes.

## Design reference

For the initial scope and the source-management ideas adapted from Khoj, see [references/design-context.md](references/design-context.md). This is background for evolving the skill, not a runtime dependency.
