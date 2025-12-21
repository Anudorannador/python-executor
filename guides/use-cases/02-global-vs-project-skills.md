# Use Case 2: Project Skills vs Global Skills (Reusable Templates Without Project Leakage)

## Scenario

In your day-to-day work, incident debugging produces valuable knowledge:

- You learn project-specific details (service names, tables, topics, cache keys, naming conventions).
- You also learn reusable patterns (how to debug data correctness, how to build evidence, how to write postmortems).

You want both outcomes:

1) **Project skills** that help an LLM operate effectively in one repo.
2) **Global skills** that are generic templates you can reuse in a brand-new project.

The key constraint is avoiding “project leakage”: the global skill should not carry project-specific prefixes (e.g., `abc_`) or internal naming into future projects.

## How this guide helps

This guide is **prompt-first**: it shows how to instruct an LLM to produce both project learn and global learn from the same incident evidence.

- **Project skills**: deep understanding of one codebase (names, tables, topics, domain semantics).
- **Global skills**: portable templates that do not leak project-specific prefixes (e.g., `abc_`).

`python-executor (pyx)` supports this well because it:

- produces reproducible evidence via MANIFEST_IO runs
- generates skills as file packages (`SKILL.md` + `references/`)

## Copy/Paste Prompt Template (Two-Layer Learn Output)

Paste this after an incident investigation is complete.

```text
You are my learning and documentation assistant.

Goal: produce two outputs from the incident evidence.

Hard requirements:
- Do not invent facts. Use only evidence from MANIFEST_IO outputs and the investigation log.
- Produce two deliverables:
  1) Project learn (repo-scoped): may include project-specific names.
  2) Global learn (portable template): MUST NOT include project-specific prefixes, service names, internal URLs, or proprietary repo layout.

Inputs you can use:
- temp/<topic>.<run_id>.inspect.md
- manifests/logs/outputs referenced in that log

Global de-projecting policy:
- Replace any project prefix like "abc_" with <PROJECT_PREFIX>_.
- Replace service/module names with <SERVICE> / <MODULE>.
- Replace table names with <TABLE_...>.
- Replace topic names with <TOPIC_...>.
- Convert concrete queries into templates with placeholders.
- Keep environment access generic: localhost tunnels + env vars.

Output format:
- For project learn: list concrete checklists, entrypoints, tables/topics/key patterns.
- For global learn: produce a reusable playbook + template checklists + placeholder mapping table.

Start by asking me for:
- The project prefix (e.g. "abc")
- Which parts should remain project-only vs globally reusable
```

## How to Store Each Layer

### Project skills (repo-scoped)

Use project skills to capture:

- domain terms and naming conventions
- exact tables/topics/cache key patterns
- code entrypoints and module boundaries
- invariants unique to the system

Recommended:

- Commit public-safe skills to the repo under `skills/`.

### Global skills (user-scoped)

Use global skills to capture:

- investigation playbooks (DB/Redis/Kafka)
- artifact conventions (inputs/outputs/manifests)
- postmortem templates
- generic checklists and placeholder-driven templates

Recommended:

- Store in your user-level Claude skills folder:
  - Windows: `%USERPROFILE%\\.claude\\skills`
  - Linux/macOS: `$HOME/.claude/skills`

## Copy/Paste Commands (Generate Skills)

Global skills install (machine-specific; local):

- Windows (cmd)
  - `pyx gs --skill all --privacy local -o "%USERPROFILE%\\.claude\\skills"`
- Windows (PowerShell)
  - `pyx gs --skill all --privacy local -o "$env:USERPROFILE\\.claude\\skills"`
- Linux/macOS
  - `pyx gs --skill all --privacy local -o "$HOME/.claude/skills"`

Repo skills (public-safe; commit to repo):

- `pyx gs --skill all --privacy public -o skills`

## De-Projecting Policy (Global Skills)

This policy is the most important part. If the global skill violates this, it is not reusable.

### 1) Replace identifiers with placeholders

- `abc_*` → `<PROJECT_PREFIX>_*`
- service names → `<SERVICE>`
- module names → `<MODULE>`
- tables → `<TABLE_...>`
- Kafka topics → `<TOPIC_...>`
- Redis keys → `<KEY_PATTERN_...>`

### 2) Preserve rules, not values

Do not encode:

- “the topic is named `abc.order.created.v1`”

Encode:

- “topics are named `<PROJECT_PREFIX>.<domain>.<event>.v<version>`”

### 3) Convert concrete queries into templates

Keep the structure, parameterize the values:

- `WHERE user_id = <USER_ID>`
- `AND ts BETWEEN <START_TS> AND <END_TS>`

### 4) Keep environment access generic (localhost tunnels)

Because access is via TCP forwarding:

- always use localhost/127.0.0.1
- treat ports/URLs as inputs (env vars or input JSON)
- always run fingerprint checks first

Common URL-style env vars (generic):

- `MYSQL_<ENV>_URL` (or `DB_<ENV>_URL`)
- `REDIS_<ENV>_URL`
- `KAFKA_<ENV>_BROKERS`

Avoid embedding project prefixes in env var names in global skills (do not hardcode `ABC_MYSQL_URL`).

### 5) Remove non-transferable org details

Global skills should not embed:

- internal dashboards/URLs
- internal ticketing system details
- team/oncall specifics

Instead, encode requirements:

- “Link to the relevant dashboard.”
- “Record the incident ID.”

## Acceptance Checklist (Global Skill)

A global skill is acceptable only if:

- it contains zero project identifiers (prefixes, service names, repo paths)
- it includes a placeholder mapping table
- it includes a reusable investigation playbook (fingerprint → DB → Redis → Kafka)
- it is written so a new project can “fill in blanks” and reuse the template
