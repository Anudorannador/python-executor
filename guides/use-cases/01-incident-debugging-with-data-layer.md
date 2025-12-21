# Use Case 1: Incident Debugging With Data-Layer Access (DB/Redis/Kafka)

This guide describes a common workflow:

- A teammate reports a bug or incorrect data in an internal system.
- You need to investigate by connecting to the data layer (database, Redis, Kafka, etc.).
- Your environment uses TCP forwarding, so all connections are `localhost:<port>`.
- You must produce (a) a clear explanation for the teammate and your leader and (b) durable evidence and reusable knowledge so the next investigation is faster.

This is a great match for `python-executor (pyx)` because it turns an investigation into **reproducible artifacts**.

## Goals

- **Reproduce** the issue and bound the impact.
- **Prove** conclusions with a file-based evidence trail.
- **Fix** the issue (or mitigate) safely.
- **Communicate** clearly (teammate + leader).
- **Learn**: extract a reusable workflow so the LLM (and you) don’t restart from scratch next time.

## What to Generate (Three Outputs)

### 1) Evidence (MANIFEST_IO artifacts)

For every meaningful check, run a script via `pyx run` and produce:

- a script (`temp/<task>.py`)
- input JSON (`temp/<task>.input.json`)
- a manifest (`temp/<task>.<run_id>.manifest.json`)
- a log (`temp/<task>.<run_id>.log.txt`)
- one or more output files (CSV/JSON/TXT)

This makes your investigation reproducible and reviewable.

### 2) Investigation log (inspect)

Create a single narrative file for the incident:

- `temp/<topic>.<run_id>.inspect.md`

The log should link to manifests/logs/outputs for evidence.

### 3) Summary + Learn

- A short, leader-friendly summary (status/impact/root cause/actions).
- A “learn” output that captures the reusable investigation workflow.

## Recommended Workflow

### Step 0: Confirm the environment (TCP forward)

Because your data layer is accessed via local TCP forwards, treat the following as **inputs**, not assumptions:

- Which environment is this (prod/staging)?
- Which tunnels are active?
- Which local ports map to which systems?

Recommended (generic) env vars:

- `DB_HOST=127.0.0.1`
- `DB_PORT=<port>`
- `REDIS_HOST=127.0.0.1`
- `REDIS_PORT=<port>`
- `KAFKA_BROKERS=127.0.0.1:<port>` (or a comma-separated list)

Do not write secrets to disk. Read them from env.

### Step 1: Create a topic + run id and start an inspect log

1. `pyx ensure-temp --dir "temp"`
2. Create `temp/<topic>.<run_id>.inspect.md`

Use this structure:

- **Problem statement** (what the teammate observed)
- **Expected behavior**
- **Scope** (time window, user IDs, entity IDs)
- **Hypotheses** (what could cause it)
- **Steps + evidence links** (each step references a manifest)
- **Root cause**
- **Mitigation / Fix**
- **Prevention**

### Step 2: Run “fingerprint” checks first (avoid wrong-environment mistakes)

Before deep debugging, produce fingerprints that prove what you connected to.

Examples (generic):

- DB: current database/user/time, version
- Redis: `INFO server` + keyspace summary
- Kafka: cluster/broker metadata + topic list subset

The output of these checks should be committed as artifacts for the incident (via MANIFEST_IO).

### Step 3: Investigate source-of-truth first, then cache, then async

A practical ordering for “data is wrong” problems:

1. **Database (source of truth)**
   - verify the canonical record(s)
   - check timestamps/timezone boundaries
   - check read replica lag if applicable
2. **Redis (cache / derived views)**
   - confirm key existence, TTL, serialization version
   - compare cached value vs DB value
3. **Kafka (async pipeline)**
   - confirm messages were produced
   - confirm consumer group offsets and lag
   - validate idempotency / de-dup logic if duplicates exist

Each step is its own `pyx run` task with its own manifest.

### Step 4: Record diffs, not just raw results

Make the output easy to interpret by writing explicit diffs:

- “DB value vs cache value” diff JSON
- “expected vs actual” CSV
- “message count per partition” table

Your teammate/leader should not need to parse raw logs.

### Step 5: Produce the two summaries (teammate + leader)

Use two audiences in one doc, or two short docs:

- **Teammate summary**: what happened, workaround, ETA, data correction plan
- **Leader summary**: impact, root cause, detection gap, prevention actions (owners + dates)

If you already have an incident log, the summary is mostly selecting and compressing.

### Step 6: Run “learn” to make it reusable

After you finish:

- extract a reusable investigation workflow as a `learn` output
- keep project-specific details in the project skill
- extract generic patterns into a global skill (see Use Case 2)

## Suggested Script Conventions

Even if you don’t standardize code heavily, standardize **inputs and outputs**:

- Input JSON should always include:
  - `time_window` (`start`, `end`, timezone policy)
  - `entity_ids` (user/order/etc.)
  - `notes` (free text)
- Output files should have predictable names:
  - `fingerprint.*.json`
  - `db_rows.*.csv`
  - `redis_value.*.json`
  - `kafka_offsets.*.json`
  - `diff.*.json`

This makes learn extraction and reuse much easier.

## Why this works well with pyx

- MANIFEST_IO makes investigations **auditable**.
- `inspect` makes the narrative **repeatable**.
- `summary` makes communication **fast**.
- `learn` turns repeated incident work into **templates**.
