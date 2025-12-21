# Use Case 2: Project Skills vs Global Skills (Reusable Templates Without Project Leakage)

## Scenario

In your day-to-day work, incident debugging produces valuable knowledge:

- You learn project-specific details (service names, tables, topics, cache keys, naming conventions).
- You also discover reusable patterns (how to debug data correctness, how to build evidence, how to write postmortems).

You want both outcomes:

1) **Project skills** that help an LLM operate effectively inside one repo.
2) **Global skills** that are generic templates you can reuse in a brand-new project.

The key constraint is avoiding **project leakage**: a global skill must not carry project-specific prefixes (e.g., `abc_`) or internal naming into future projects.

## What this guide is (and is not)

This guide is **prompt-first**. It teaches you how to instruct an LLM to use the **learn workflow** to produce two *new* skill packages after an incident:

- a **project-derived skill** (repo-specific)
- a **global-derived skill** (portable)

Important clarification:

- `pyx gs` generates the **pyx tool skills** (e.g. `pyx`, `inspect`, `manifest`, `learn`, `summary`). Those are the “operating manual” that teaches an LLM how to use `python-executor`.
- Your **project skill** and **global skill** are *derived outputs* created by running the **learn** process on real incident evidence (investigation log + manifests/logs/outputs).

## The Core Workflow (Two Outputs From One Incident)

After you finish debugging and have evidence on disk:

1) Produce a **project skill** that preserves the repo’s real names and semantics.
2) Produce a **global skill** that is a reusable template with placeholders (no project identifiers).

Both should be grounded in the same evidence:

- `temp/<topic>.<run_id>.inspect.md`
- the referenced manifests/logs/outputs

## Copy/Paste Prompt Template (Learn → Project Skill + Global Skill)

Paste this after an incident investigation is complete.

```text
You are my learning and documentation assistant.

Goal: derive two reusable skill packages from the incident evidence.

Hard requirements:
- Do not invent facts. Use only evidence from MANIFEST_IO outputs and the investigation log.
- Produce two deliverables:
  1) Project skill (repo-scoped): may include project-specific names.
  2) Global skill (portable template): MUST NOT include project prefixes, service/module names, internal URLs, proprietary repo paths, or internal ticketing details.

Inputs you can use:
- temp/<topic>.<run_id>.inspect.md
- manifests/logs/outputs referenced in that log

Process:
1) Ask me for the project prefix (e.g. "abc") and what must stay project-only.
2) Build a "fact table" from evidence (what was checked, what was found, what fixed it).
3) Generate the Project Skill package:
   - SKILL.md + (optional) references/ with concrete, project-specific conventions.
4) Generate the Global Skill package:
   - SKILL.md + (optional) references/ with placeholders and templates.
5) Provide a short review checklist for me to confirm no leakage in the global skill.

Global de-projecting policy:
- Replace any project prefix like "abc_" with <PROJECT_PREFIX>_.
- Replace service/module names with <SERVICE> / <MODULE>.
- Replace table names with <TABLE_...>.
- Replace topic names with <TOPIC_...>.
- Replace Redis keys with <KEY_PATTERN_...>.
- Convert concrete queries into templates with placeholders.
- Keep environment access generic: localhost tunnels + env vars.

Output format:
- For the project skill: concrete checklists, real entrypoints, real tables/topics/key patterns.
- For the global skill: reusable playbook + template checklists + placeholder mapping table.
```

## What to Put in Each Layer

### Project-derived skill (repo-scoped)

Include:

- real domain terms and naming conventions
- real tables/topics/cache key patterns
- code entrypoints/module boundaries
- invariants unique to the system

Suggested outcome:

- A skill directory you can keep in the repo (project-specific).

### Global-derived skill (portable)

Include:

- investigation playbooks (fingerprint → DB → Redis → Kafka)
- artifact conventions (inputs/outputs/manifests)
- postmortem templates
- placeholder-driven templates that can be “filled in” in a new project

## Environment/Connection Guidance (Keep It Reusable)

Because access is commonly via TCP forwarding:

- assume localhost/127.0.0.1 endpoints
- treat ports/URLs as inputs (env vars or input JSON)
- require fingerprint checks first

If your org uses URL-style env vars, keep them generic in the global skill:

- `MYSQL_<ENV>_URL` (or `DB_<ENV>_URL`)
- `REDIS_<ENV>_URL`
- `KAFKA_<ENV>_BROKERS`

Avoid embedding project prefixes in env var names in global skills (do not hardcode `ABC_MYSQL_URL`).

## De-Projecting Policy (Global Skill)

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

### 4) Remove non-transferable org details

Global skills should not embed:

- internal dashboards/URLs
- team/oncall specifics
- proprietary repo layout details

Instead, encode requirements:

- “Link to the relevant dashboard.”
- “Record the incident ID.”

## Acceptance Checklist (Global Skill)

A global-derived skill is acceptable only if:

- it contains zero project identifiers (prefixes, service names, repo paths)
- it includes a placeholder mapping table
- it includes a reusable investigation playbook (fingerprint → DB → Redis → Kafka)
- it is written so a new project can fill in blanks and reuse the template
