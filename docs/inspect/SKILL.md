---
name: inspect
description: "Structured investigation with a persistent markdown log and evidence-first execution. Use when: investigating a user question, auditing behavior, verifying dependencies, or using MCP tools. Triggers: inspect, investigate, analyze, audit, verify, deepwiki. Default mode: MANIFEST_IO."
version: 0.1.0
---

# Inspect

Run investigations in a reproducible, evidence-first way.
**Default and required: MANIFEST_IO mode.**
All investigation artifacts must be written to files.

## Depends On (Soft)

Load these skills alongside `inspect`:

- `manifest` - MANIFEST_IO contract and workflow
- `learn` - skill extraction workflow and summary reference

## Current Environment

- **OS**: Windows (AMD64)
- **Shell**: powershell
- **Python**: 3.12.12
- **pyx version**: 0.1.0

## Investigation Log (Mandatory)

When the user asks a question, create a dedicated markdown log file.
You must call `pyx ensure-temp --dir "temp"` first.

**Naming:** `temp/<topic>.<run_id>.inspect.md`

- `<topic>`: short, lowercase, use `-` as separator (e.g. `redis-timeout`)
- `<run_id>`: reuse the pyx run id when possible

The log must be written in English and must include:

- The user question (verbatim)
- The LLM understanding (assumptions + constraints)
- The investigation steps (what you did and why)
- Evidence (paths to manifests/logs/outputs)
- Final answer
- Open questions / next actions

## MANIFEST_IO (Required)

If you need to look up or compute anything (files, data, web, dependency info):

1. Create a task script in `temp/`.
2. Read input from a JSON file.
3. Write outputs to files and index them in a manifest.
4. Print a short summary only (paths + sizes).

See the `manifest` skill for the full spec.

## MCP Tools (Only If Requested)

If the user explicitly requests MCP tools (e.g. DeepWiki):

1. **Check available MCPs** in the current environment.
2. Confirm with the user which MCP you will use.
3. Record the MCP name, query, and results (or output file paths) in the investigation log.

If the requested MCP is not available, stop and ask the user how to proceed.

## Code Verification

When the user asks to verify against the *actual code* in the current environment:

- Treat it as a **code verification** task, not a best-guess answer.
- Use MANIFEST_IO scripts to collect evidence and include paths/sizes in the log.
- Prefer lockfiles and installed artifacts over assumptions.

Typical targets:

- Python venv: `.venv/`, `site-packages/`, `pip list`, `pip show <pkg>`
- Node.js: `package.json`, lockfile, `node_modules/`
- Rust/Cargo: `Cargo.toml`, `Cargo.lock`, `target/`

Documentation targets (only when needed):

- Official docs (e.g. Microsoft Docs) to confirm API contracts
- DeepWiki/repo docs to confirm intended usage patterns

If using docs/MCP tools:

- Confirm the source/version with the user
- Record the MCP name + query
- Save evidence to files via MANIFEST_IO and link paths in the investigation log

See: [Code Verification](references/code-verification.md)

## Rules (Strict)

- **English only** in outputs and logs.
- **No direct network fetch in chat.** Use MANIFEST_IO and check proxy env vars first.
- **No guessing resource connections.** List env vars and ask user to confirm.

## References

- `manifest` skill - MANIFEST_IO Details
- [Investigation Log Template](references/investigation-log-template.md)
- [Code Verification](references/code-verification.md)
