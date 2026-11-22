# Initial design context

This first version extends the learning approach in `source-code-learning`: bounded questions, precise source evidence, observable mastery, and resumable progress. Study Studio adds mixed local documents, several repositories per topic, and automatic synthesis of reusable question notes.

Khoj is a reference for associating multiple source types with a continuing conversation. Its documentation separates source ingestion/sync from the chat interface:

- [Supported sources](https://github.com/khoj-ai/khoj/blob/ae229ca894c0b80ad84664afcfdde523b5e87057/documentation/docs/features/all-features.md) lists Markdown, PDF, plaintext, and GitHub repositories.
- [Sharing data](https://github.com/khoj-ai/khoj/blob/ae229ca894c0b80ad84664afcfdde523b5e87057/documentation/docs/data-sources/share_your_data.md) describes one-off uploads and ongoing source synchronization.

For Study Studio, a resource registry and source locators provide the initial association mechanism. Direct reading keeps existing resources usable in place. This is a design adaptation, not an implementation of Khoj indexing or synchronization. No Khoj runtime or code is bundled.

The initial workflow remains deliberately small: `question -> evidence-backed answer -> reusable note -> goal/progress update`. Refine closure signals, goal hierarchy, and note organization from actual learning sessions.
