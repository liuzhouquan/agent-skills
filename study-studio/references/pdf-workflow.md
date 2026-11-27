# PDF reading and extraction

Use this workflow when a study includes a PDF. The goal is to find and read relevant passages efficiently while retaining reliable page-level evidence.

## Detect and choose a tool

1. Check whether the current environment already has a usable PDF text extractor or reader. Prefer a local command-line or Python library that does not upload the document.
2. For ordinary selectable-text PDFs, prefer a lightweight extractor such as Poppler `pdftotext` with layout preservation. If it is absent, tell the user what is missing and offer to install/configure a local extractor. Proceed with installation only after the user agrees. Use the environment's available package manager and normal permissions; do not silently use elevated access or change global configuration.
3. For scanned PDFs, complex reading order, tables, or equations, explain that plain extraction may lose information. Offer an OCR/layout-aware option when needed, describe its size and whether it runs locally, and ask before installing it. Do not send source documents to a hosted converter without explicit agreement to that data transfer.
4. If the user declines or installation is unavailable, continue with available PDF-reading/rendering tools and state any limitation. Do not block unrelated Markdown, text, or code study.

When asking, make the choice concrete: name the proposed tool, the reason it helps, whether it is local, and any material installation requirement. After consent, install only the needed tool, then verify it against a small page/sample from the user's PDF. Report the installed tool and the verification result.

## Extract and read selectively

- Extract text with page boundaries preserved. If the extractor emits plain text, wrap it in Markdown with clear `## PDF page N` headings rather than implying semantic headings that were not present in the PDF.
- Store generated text under `studyspace/derived/pdf-text/<resource-id>.md` by default. Do not modify the source PDF. Register the derivative path, extractor name/version when available, and source hash in the PDF entry in `assets.json`.
- For very large documents, avoid eagerly converting or reading all pages unless the user asks. Start with metadata, table of contents, or targeted page ranges; search the derivative for relevant terms and inspect nearby passages. Extract/cache the rest only when useful.
- Load only the relevant excerpts into the active context. The derivative makes search and page navigation cheaper; it does not make the entire PDF free to include in every prompt.
- Cite the original PDF's page number in notes and answers. Preserve both PDF page index and printed page label when they differ or when the printed label is material.
- Inspect the original rendered page for figures, diagrams, layout-dependent tables, equations, scanned content, or suspicious extraction. Mark OCR-derived or uncertain text as such and verify important values against the page image.

## Keep the cache current

Before relying on a cached derivative, compare the PDF's current hash with `extracted_text.source_sha256`. If they differ or the source moved, regenerate the relevant extraction and recheck claims based on changed pages. Retain old notes as historical evidence and mark affected notes `needs_review` until checked. Never present a derivative as the original source.
