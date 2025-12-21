# Use Case 2: Project Skills vs Global Skills (Reusable Templates Without Project Leakage)

This guide describes a common need:

- You want **project-specific** skills that deeply understand one internal system (naming, domains, data model, service boundaries).
- You also want **global** skills that are portable and reusable across projects.
- When extracting a learnable workflow from a project, you do **not** want to carry project-specific prefixes (for example, an `abc_` prefix) into the global template.

`python-executor (pyx)` is designed to support this split:

- It generates skills as **file packages** (`SKILL.md` + `references/`).
- It keeps “run evidence” as **MANIFEST_IO artifacts**.
- It can regenerate skills consistently (so you can keep the global and project layers aligned).

## The Two Layers

### Layer A: Project skills (repo-scoped)

Use project skills to capture:

- domain terms, service/module names, project-specific naming conventions
- exact tables/topics/cache key patterns
- “how this system works” mental models
- operational constraints unique to the system

Recommended storage:

- Commit to the repo under `skills/` (public-safe)

Example:

- `skills/pyx/`
- `skills/inspect/`
- `skills/manifest/`
- `skills/learn/`
- `skills/summary/`

### Layer B: Global skills (user-scoped)

Use global skills to capture:

- reusable workflows and templates
- generic investigation playbooks (DB/Redis/Kafka)
- artifact conventions (inputs/outputs/manifests)
- postmortem structures and checklists

Recommended storage:

- Your user-level Claude skills folder
  - Windows: `%USERPROFILE%\.claude\skills`
  - Linux/macOS: `$HOME/.claude/skills`

## How to Generate Skills for Global Use

If you want a rich, machine-specific snapshot (for example, when you want local environment details embedded):

- Windows (cmd)
  - `pyx gs --skill all --privacy local -o "%USERPROFILE%\.claude\skills"`
- Windows (PowerShell)
  - `pyx gs --skill all --privacy local -o "$env:USERPROFILE\.claude\skills"`
- Linux/macOS
  - `pyx gs --skill all --privacy local -o "$HOME/.claude/skills"`

If you want public-safe output suitable for committing to a repo:

- `pyx gs --skill all --privacy public -o skills`

## The Core Problem: Avoiding Project Leakage

When you learn from a project incident, you will naturally encounter:

- project prefixes (e.g. `abc_*`)
- internal service names and repo structure
- internal URLs, dashboards, ownership lists

These are valuable in project skills but harmful in global skills.

The solution is to enforce a “de-projecting” policy when writing global skills.

## A Practical De-Projecting Policy (Global Skills)

### 1) Replace identifiers with placeholders

In global skills:

- Replace project prefix `abc_` with `<PROJECT_PREFIX>_`
- Replace service names with `<SERVICE>`
- Replace topic names with `<TOPIC_...>`
- Replace table names with `<TABLE_...>`

Examples:

- `abc_orders` → `<PROJECT_PREFIX>_orders`
- `abc.order.created.v1` → `<TOPIC_ORDER_CREATED>`
- `orders_v2` → `<TABLE_ORDERS>`

### 2) Preserve rules, not values

Do not encode “the table is named X”.
Encode “the system uses a stable naming rule”:

- “Topics are named `<PROJECT_PREFIX>.<domain>.<event>.v<version>`.”
- “Redis keys include `<PROJECT_PREFIX>:<domain>:<entity_id>`.”

### 3) Convert concrete queries into query templates

Keep the structure but parameterize values:

- `WHERE user_id = <USER_ID>`
- `AND ts BETWEEN <START_TS> AND <END_TS>`
- `AND env = <ENV>`

### 4) Keep environment access generic

Because your data access is via TCP forwarding:

- Always use `localhost` / `127.0.0.1`
- Treat ports as inputs (env vars or input JSON)
- Always run “fingerprint” checks first

### 5) Remove non-transferable org details

Global skills should not embed:

- internal URLs or dashboards
- internal ticket systems
- specific team names or on-call rotations
- proprietary repo layout details

Instead, encode the requirement:

- “Link to the relevant dashboard.”
- “Record the ticket/incident ID.”

## Recommended Workflow: Produce Both Outputs

After an incident:

1. Write the project-specific learn artifact (project skill update)
2. Write a global template learn artifact (de-projected)

You can treat it as “two deliverables from the same evidence”.

## What to Put in Each Layer (Quick Checklist)

Project skills:

- entrypoints and module names
- data dictionary (tables/columns)
- canonical topics and message schemas
- business-specific invariants

Global skills:

- incident checklist (fingerprint → DB → Redis → Kafka)
- artifact naming conventions for MANIFEST_IO
- diff-first outputs (expected vs actual)
- postmortem template (impact/root cause/prevention)

## Why this pairing works

- Project skills speed up work inside the same codebase.
- Global skills provide safe templates you can reuse anywhere.
- MANIFEST_IO evidence makes both layers credible and easy to maintain.
