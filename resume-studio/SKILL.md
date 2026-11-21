---
name: resume-studio
description: Create and edit structured resumes with independent HTML templates, a local live editor, and browser-based interaction with Codex CLI. Use for resume writing, template switching, preview, and HTML export.
---
# Resume Studio

Keep resume facts and presentation independent. Use this skill's runnable local editor instead of asking the user to hand-format HTML.

## Start

Launch from the skill directory:

```sh
python3 scripts/serve.py --workspace /absolute/path/to/resume-workspace --port 8765
```

Open the printed localhost URL. Python 3 and a logged-in `codex` CLI on PATH are required for Agent requests; editing and export work without Codex. The server stays attached until stopped. Pick another port if occupied.

The workspace owns the private `studio.sqlite3` library and `history/`; legacy `resume.json` and `presentation.json` are imported once without modifying originals; the skill owns reusable code and templates. Never put a person's resume in the bundled demo. Existing workspace data takes precedence over the demo. Avoid running two servers against the same workspace.

## Private memory and versions

Default data location: `~/projects/resume-workspace`, outside this skill. Reuse the same workspace on later invocations to restore the last open resume. Do not move personal facts, conversation logs, drafts, generated HTML or exported PDFs into the skill's references or assets. A custom `--workspace` remains supported. The server creates a workspace `.gitignore` that excludes all private files; it does not remove already tracked files from Git.

The local library automatically saves draft edits after a short debounce, including template settings, pasted source, user instructions, recent Agent conversation and unapplied candidate. The UI shows save failures and warns before leaving with unsaved changes. “我的简历库” creates independent resumes, copies the current draft, renames and switches documents. “存档当前版本” creates a complete timestamped snapshot named from the current resume. “导出完整档案” downloads the resume, template settings and session memory as JSON; “导出内容” exports only resume facts. Selecting an archive switches the entire working context: resume fields, candidate, Agent conversation and future requests. The state being left is preserved as another ordinary timestamped archive. Versions include content, presentation and memory. Conflict revisions block another tab from silently overwriting newer data.

Use the same data directory across sessions; launching against a temporary directory intentionally creates a separate library. Do not infer facts from unrelated stored resumes or send an entire library to a model; only the current request and current resume context are submitted. Read [references/data-contract.md](references/data-contract.md) for the storage/API details when maintaining persistence.

## Content and templates

Read [references/data-contract.md](references/data-contract.md) before importing material or editing the renderer. Turn user facts into plain strings and bullet arrays. Preserve uncertainty; do not invent metrics, employers, dates, credentials, or ownership. Ask for necessary missing facts or leave obvious placeholders.

- Change content through the editor or the authenticated draft API. SQLite is the source of truth after migration; legacy JSON files are not live mirrors.
- Change template choice and density in the toolbar; presentation is stored separately from facts inside each draft.
- Add reusable templates as CSS files under `assets/studio/templates/` and entries in `manifest.json`. Templates share the semantic renderer and must not contain personal facts.
- Items can be hidden in the editor without deletion. Hidden items stay in local drafts and archives but do not render, export, print, or enter Codex requests; restoring visibility brings them back. Do not inject HTML, Markdown markers, inline styles, or manual line breaks into content for layout. When overflow occurs, first adjust template/density or edit wording with the user's intent intact.

Paste existing text or Markdown into “粘贴内容，让 Agent 整理”; choose replace to create a new resume from those facts only, or merge to enrich the current document. Both return a reviewable candidate without overwriting the current resume.

The editor offers plain text forms and optional in-preview editing for profile, section and item text; changes update structured content and autosave. Candidate previews remain read-only. It offers live preview, section/item management, JSON import/export, local save, standalone HTML export, and browser print. A print preview is not proof of correct PDF pagination: inspect resulting PDF if a PDF deliverable is requested.

## Agent interaction

The browser sends current resume, recent conversation, and request to the local Python server. The server invokes `codex exec` using a fixed argument list, a read-only sandbox and structured output. It returns explanation and a candidate resume, never directly overwriting the document. A visible busy state remains on the submit button until the CLI finishes. Successful candidates open in the preview automatically; switch back to the current draft or view both side by side. The user can discard or apply the candidate; applying is blocked if content changed after the request. The Agent changes content only, not templates.

At startup, query the CLI app-server `model/list` and select its recommended model unless `--model` was explicitly supplied. Do not rely on cached model aliases. Display the discovered list and connection status in the UI; “检查连接” sends a real minimal request. This does not change global CLI configuration.

The optional model field overrides the model for one request; `--model NAME` sets a server default. If the provider rejects the configured model, use a name supported by that account rather than guessing aliases. Use the existing CLI login and configured model; do not copy credentials into this skill or the browser. Submitted content is sent to the CLI's configured model provider. The server binds only to loopback and does not need remote hosting. Do not bypass sandbox or approvals to work around local errors. Surface the error and keep manual editing available.

## Checks

Run `python3 scripts/check.py` after changing Python, data, or templates. For UI changes, exercise edit → save → reload, template switching without content changes, import/export, and Agent candidate preview/apply including stale-candidate rejection. Use the real CLI only when requested or needed, because it consumes model usage. The launch script alone does not install this skill into agent discovery; use the user's existing skill installation convention when asked.
