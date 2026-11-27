# Initial design context

This first version extends the learning approach in `source-code-learning`: bounded questions, precise source evidence, observable mastery, and resumable progress. Study Studio adds mixed local documents, several repositories per topic, and grouped drafts of questions and tentative ideas and later consolidation into reusable topic notes.

Khoj is a reference for associating multiple source types with a continuing conversation. Its documentation separates source ingestion/sync from the chat interface:

- [Supported sources](https://github.com/khoj-ai/khoj/blob/ae229ca894c0b80ad84664afcfdde523b5e87057/documentation/docs/features/all-features.md) lists Markdown, PDF, plaintext, and GitHub repositories.
- [Sharing data](https://github.com/khoj-ai/khoj/blob/ae229ca894c0b80ad84664afcfdde523b5e87057/documentation/docs/data-sources/share_your_data.md) describes one-off uploads and ongoing source synchronization.

For Study Studio, a resource registry and source locators provide the initial association mechanism. Direct reading keeps existing resources usable in place. This is a design adaptation, not an implementation of Khoj indexing or synchronization. No Khoj runtime or code is bundled.

The initial workflow remains deliberately small: `question/idea -> grouped draft -> assess maturity and plan impact -> agreed note or authorized plan change -> progress update`. Refine closure signals, goal hierarchy, and note organization from actual learning sessions.

Interview verification draws on the inspected LLMInternSkill reference: follow the learner's claims into inputs/outputs, tradeoffs, scenarios and evidence, then turn gaps into bounded learning tasks. Study Studio adapts this into one-question-at-a-time practice within current progress, rather than a full resume-audit or project-scout workflow. The reference skill is not a runtime dependency.
