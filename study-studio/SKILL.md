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
- Read existing `goal.md`, `assets.json`, and relevant notes before continuing. Keep unresolved questions and the next action so another session can resume. If no matching workspace can be identified, ask for its location rather than inventing prior progress.
- Initialize only the small structure in [references/studyspace.md](references/studyspace.md). Resources can stay where they are. Register paths rather than relocating or copying files by default. Use `resources/` for user-provided copies when useful or requested.

## Goals and learning context

Maintain `goal.md` as a hierarchy of goals and smaller questions with stable IDs, a target mastery level, status, achieved level, evidence links, remaining gaps, and next action. Capture relevant learner background, constraints, and intended applications only when supplied by the user; identify tentative assumptions as such. Do not infer personal traits from questions.

Start with the user's current question. For a broad request, briefly inspect the supplied resources and offer a few bounded learning directions. Keep at most one learning unit in progress; other goals can remain pending. A unit should usually fit a focused session rather than require reading an entire project or book.

Use these mastery levels per goal:

1. **Knows its purpose:** learner can explain the problem, use cases, and main inputs and outputs.
2. **Can explain it:** learner can reconstruct the important reasoning or implementation, including key decisions and boundaries, using evidence.
3. **Can apply, modify, or reproduce it:** learner independently completes a meaningful application or change and reproduces the outcome with an appropriate check or artifact.

Separate answer resolution from learner mastery. An assistant explanation or experiment can resolve a question without proving that the learner has mastered it. Award levels from learner explanations, predictions, exercises, or artifacts with supporting evidence. Mark a goal completed only when its target has evidence; preserve partial progress without forcing a quiz after every question.

## Read and explain with evidence

Use local resources as primary evidence and inspect only the paths or passages needed for the question. Read each source using its appropriate tools; the skill does not require an indexing service, vector database, or Khoj installation.

- **Code:** trace entry points, symbols, callers/callees, state changes, and data flow. Cite repository ID, file path, symbol, and useful line numbers. Inspect tests and configuration where they establish behavior. Use small code or concept maps when they clarify the current question.
- **PDF:** extract text with available PDF tools; preserve page references. For diagrams, equations, tables, or unreliable extraction, inspect rendered pages. Distinguish PDF page index from printed page number when they differ. If extraction or OCR is unavailable, explain the limitation rather than fabricate content.
- **Markdown/text:** read the relevant sections and cite the resource ID, heading, and useful line numbers. Follow linked resources only as needed.
- **Multiple resources:** identify which source supports each conclusion. Surface conflicting versions or assumptions rather than silently combining incompatible claims.

Record resource identity in `assets.json`: canonical path and type; for Git sources, sanitized remote, branch, and commit; for documents, available version information and a content hash when used. Never store credentials in resource metadata. On resume, check availability and changes to sources supporting the current question; recheck affected conclusions and mark stale notes `needs_review`. Preserve historical evidence instead of rewriting it as current fact. If a path moved, update it after locating the actual resource.

Answer directly, then explain the smallest useful evidence chain. Distinguish source facts, runtime observations, and inference. Run a focused experiment when needed and feasible; use an isolated scratch area for exercises and avoid treating unrun code as a verified result. A useful loop is `predict -> inspect -> observe -> explain -> apply -> verify`, adapted to the learner's question.

## Automatically synthesize reusable notes

Treat use of this skill as authorization to maintain the selected local studyspace. Once a question has a supported answer and no material unanswered part remains, synthesize or update a note without asking the user to request saving again. Signals include learner confirmation, a shift to the next question, or a complete supported answer. If closure is unclear, preserve a provisional note with explicit open questions; do not declare mastery or certainty merely because the conversation moved on.

A note should preserve the learner's question and intent, a concise reusable conclusion, the explanation or trace, source locators and versions, applicability and limits, and unresolved issues. Add experiments and reproduction steps only when performed or clearly label them as proposals. Capture user corrections and useful explanations without saving every conversational turn or duplicating the transcript.

- Use one stable note per coherent question or tightly related group. Update an existing note for follow-ups; link a separate note when the question becomes independently useful.
- Distinguish user statements from assistant synthesis. Retain important caveats, evidence, and changes of understanding when revising.
- Link the note to goal IDs and resource IDs. Update the note index in `note/README.md` and progress in `goal.md` after meaningful resolution or a goal change.
- At interruption or session end, persist the current question, known evidence, remaining uncertainty, and next action even if the question remains open.
- Briefly report what was saved and its path. If saving fails, state that it failed and retain the intended content in the response; do not claim persistence.

Keep the skill itself separate from personal study data. Invoking it authorizes local note maintenance, not publishing, committing, or pushing a learner's notes. Respect explicit requests to skip saving or keep particular information out of notes.
