# python-executor (pyx)

`pyx` is a local, cross-platform executor for LLM/Agent workflows.
It is built for **evidence-based debugging and repeatable prompting**: run work via MANIFEST_IO (files + manifest), keep an inspect log, and turn incident work into reusable skills.

Start with these prompt-first use cases:

- [Incident debugging with data-layer access](guides/use-cases/01-incident-debugging-with-data-layer.md)
- [Project skills vs global skills (template without project leakage)](guides/use-cases/02-global-vs-project-skills.md)
- [Migration baseline for a rewrite (Python → Rust, SQLite → Postgres)](guides/use-cases/03-migration-baseline-for-rewrite.md)

This repo is designed around three repeatable outputs:

- **Skills**: reusable, file-based rules + references (bootstrap for new sessions)
- **MANIFEST_IO runs**: scripts + input JSON + manifest + log + outputs
- **Investigation logs**: reproducible code verification and audits

## Start Here (Public Repo Workflow)

### 1) Generate the pyx Claude skill (interactive)

Run:

```bash
pyx gs
```

Behavior:

- Asks `public` vs `local` privacy mode (default: public)
- Generates the `pyx` skill and prints it to the terminal
- Asks whether to save
- If saving, asks whether to overwrite existing output
- Finally asks where to save:
  - `docs\pyx` (default)
  - `%USERPROFILE%\.claude\skills\pyx`
  - custom path

### 2) Use MANIFEST_IO for all real work

**MANIFEST_IO** is the file-first execution contract:

- Inputs come from files (JSON for structured input)
- Outputs are files, indexed by a manifest
- Stdout is only a short summary (paths + sizes)
- Always check output size before loading into an LLM context

Reference: [docs/manifest/references/manifest-io.md](docs/manifest/references/manifest-io.md)

## Core Workflows

### Generate skills

Generate skill packages (Claude-style: `SKILL.md` + `references/`):

```bash
# Public-safe (recommended for committing)
pyx gs --skill all --privacy public -o skills

# Local (machine-specific; may include absolute paths/package inventory)
pyx gs --skill all --privacy local -o skills
```

Notes:

- `--skill manifest` generates the standalone MANIFEST_IO spec.
- `--skill learn` generates skill-extraction workflow + summary reference.
- `--skill pyx` focuses on execution, and depends (softly) on `manifest` + `learn`.
- `--skill inspect` focuses on investigation logs + code verification, and depends (softly) on `manifest` + `learn`.
- `--skill summary` generates leader-summary templates.
- `--skill all` generates: `manifest` + `learn` + `pyx` + `inspect` + `summary`.

### Session bootstrap (what the LLM should do first)

LLM chat history is unreliable. Treat the repo as the source of truth.

Minimal bootstrap sequence:

1. Read the `skills/pyx/` files listed above
2. Run `pyx info --json` if environment/tooling matters
3. Execute tasks via `pyx run --file` using MANIFEST_IO

### MANIFEST_IO (file-first execution)

Recommended pattern:

```bash
pyx ensure-temp --dir "temp"
# Write: temp/<task>.py
# Write: temp/<task>.input.json
pyx run --file "temp/<task>.py" --input-path "temp/<task>.input.json"
```

The executed script can read these runtime variables (auto-set by `pyx run`):

- `PYX_INPUT_PATH` (optional)
- `PYX_OUTPUT_DIR` (always)
- `PYX_OUTPUT_PATH` (always; manifest path)
- `PYX_LOG_PATH` (always)
- `PYX_RUN_ID` (always)

### Code verification + investigation logs

For “verify against actual code” tasks, use the `inspect` workflow:

- Create a dedicated log: `temp/<topic>.<run_id>.inspect.md`
- Collect evidence via MANIFEST_IO scripts
- Record manifest/log/output file paths in the log

References:

- [docs/inspect/references/code-verification.md](docs/inspect/references/code-verification.md)
- [docs/inspect/references/investigation-log-template.md](docs/inspect/references/investigation-log-template.md)

### Learn skill (extract reusable workflows)

Use the phrase “learn skill” to trigger a token-efficient workflow that:

1. Reads `temp/.history.jsonl` and recent manifests/logs
2. Summarizes headers only
3. Proposes `create` / `merge` / `overwrite`
4. Generates a SKILL preview
5. Saves only after explicit user confirmation

Reference: [docs/learn/references/learn-skill.md](docs/learn/references/learn-skill.md)

## Installation (Local Development)

```bash
git clone https://github.com/Anudorannador/python-executor.git
cd python-executor
uv tool install -e ".[full]"
```

Configure `.env`:

- Windows: `%APPDATA%\pyx\.env`
- Unix/macOS: `~/.config/pyx/.env`

Start from: `.env.example`.

Verify:

```bash
pyx info
```

## Configuration (.env)

Common `PYX_*` configuration variables:

- `PYX_UV_HTTP_PROXY`, `PYX_UV_HTTPS_PROXY`, `PYX_UV_NO_PROXY`, `PYX_UV_INDEX_URL` (uv/pip proxy/index)
See: `.env.example`

## Project structure

`docs/` contains public reference docs and example outputs.
`skills/` is the recommended committed bootstrap for LLM sessions.

```text
python-executor/
├── .env.example
├── docs/
│   ├── pyx.instructions.md
│   ├── pyx/
│   ├── inspect/
│   ├── manifest/
│   ├── learn/
│   └── summary/
├── skills/                    # Recommended committed bootstrap
│   ├── manifest/
│   ├── learn/
│   ├── pyx/
│   ├── inspect/
│   └── summary/
└── src/
    ├── pyx_core/
  └── pyx_cli/
```
