# Use Case 3: Migration Baseline for a Rewrite (Python → Rust, SQLite → Postgres)

## Scenario

You are maintaining a legacy system (often Python + SQLite) that is hitting performance limits.
You plan to rewrite it (e.g., in Rust) and likely change major components (database, frameworks, libraries).

The hardest part is not the new language.
The hardest part is safely migrating **behavior and data**:

- performance-driven rewrite (CPU and/or I/O bottlenecks)
- data volume growth
- SQLite → Postgres (types, constraints, indexing, concurrency)
- schema changes: table splits, field remapping, new keys
- historical data migration + verification

This guide focuses on creating a **baseline**: a set of reproducible artifacts that capture “what the old system does” so the new system can be validated by diff.

## What a Baseline Is (and Why It Matters)

A migration baseline is a small, durable set of **evidence and specifications** that can be re-run and re-checked:

- inputs (IDs, time windows, sample requests)
- outputs (DB rows, API responses, derived views)
- invariants (business rules that must always hold)
- contracts (schema, event formats, cache semantics)
- allowed differences (what is acceptable to differ)

Without this, a rewrite becomes opinion-based.
With this, a rewrite becomes evidence-based.

## Key Deliverables (Outputs)

When you finish baseline work, you should have:

1) **A baseline inventory**
   - critical user flows / jobs
   - key entities and IDs
   - key tables/topics/cache keys

2) **A baseline dataset**
   - a curated list of entity IDs and time windows
   - representative examples for edge cases

3) **A baseline evidence pack (MANIFEST_IO)**
   - reproducible scripts + manifests + outputs that capture current behavior

4) **A verification plan**
   - what to diff (counts, hashes, query results)
   - what differences are acceptable

## How this Works with python-executor (pyx)

Use `pyx` to keep baseline collection reproducible:

- scripts read input JSON (no “magic CLI args”)
- outputs are written to files
- a manifest indexes everything
- stdout stays short (paths + sizes)

The baseline is not “one big dump”. It is a set of small tasks with clear outputs.

## Copy/Paste Prompt Template (Baseline Kickoff)

Use this at the start of baseline creation.

```text
You are my migration-baseline assistant.

Goal: produce a baseline that captures legacy system behavior and data so a rewrite (e.g., Rust + Postgres) can be validated by diff.

Hard requirements:
- Do not read or paste large files into chat. Summarize.
- Prefer file-based outputs (MANIFEST_IO). If you need to compute anything, write a script and run it.
- Build a baseline that is stable across languages/frameworks.

Deliverables:
1) Baseline inventory (flows, entities, data sources)
2) Baseline dataset (IDs + time windows + edge cases)
3) Baseline evidence pack (manifests + outputs)
4) Verification plan (diff rules + allowed differences)

Start by asking me:
- What is being rewritten? (service name + high-level responsibilities)
- Primary motivation: performance? scale? ecosystem constraints?
- Legacy stack: language/runtime + SQLite schema location + how data is accessed
- Target stack: Rust runtime + Postgres
- Top 3 critical flows to preserve
```

## Copy/Paste Prompt Template (Repo Scan Without Blowing Context)

This prompt is for “scan the repository and summarize baseline-relevant facts” without reading everything.

```text
You are scanning a codebase to build a migration baseline.

Rules:
- Do not attempt to read the entire repo.
- Identify a small set of entrypoints and schema definitions.
- For each candidate file, read only headers or small relevant sections.
- Prefer generating a written inventory file over long chat output.

Task:
1) Identify runtime entrypoints (CLI, server, jobs).
2) Identify the legacy persistence layer:
   - SQLite file location and schema creation/migrations
   - key tables and their primary keys
   - critical queries / ORM models
3) Identify async/caching layers:
   - Kafka topic names and message schema locations
   - Redis key patterns and TTL rules
4) Produce a Baseline Inventory file:
   - baseline.inventory.md
   - include links/paths to the key source files

Before reading any file, list the top 10 candidate files/dirs you plan to inspect and ask for confirmation.
```

## Concrete Baseline Collection Tasks (MANIFEST_IO)

Below are practical tasks you can run as separate MANIFEST_IO jobs. Each task should:

- read `temp/<task>.input.json`
- write outputs to `temp/<task>.<run_id>.*`
- record everything in the manifest

### Task A: Schema snapshot

Goal: capture the legacy schema and the target schema mapping.

- Inputs:
  - path to SQLite file (or how to connect)
  - environment label
- Outputs:
  - `schema.sqlite.json` (tables/columns/indexes)
  - `schema.mapping.md` (how each legacy table maps to new tables)

### Task B: Baseline dataset selection

Goal: choose representative IDs and time windows.

- Inputs:
  - a list of “hot” entities (frequent, large)
  - a list of edge-case entities (nulls, old versions, weird states)
  - time windows (peak hours, known incidents)
- Outputs:
  - `baseline.dataset.json` (IDs + windows + rationale)

### Task C: Behavioral snapshots (legacy)

Goal: for each critical flow, record legacy outputs.

Examples:

- API response snapshots for selected requests
- DB query result snapshots for selected IDs
- Redis value/TTL snapshots for selected keys
- Kafka offsets/lag snapshots (or sample messages, if available)

Outputs should be diff-friendly:

- CSV/JSON with stable ordering
- explicit “expected vs actual” or computed checksums

### Task D: Verification rules

Goal: define how to compare old vs new.

- Counts (row counts per table, by partition/time bucket)
- Hashes (row-level checksums for stable subsets)
- Query equivalence (critical queries produce same results)
- Allowed differences (timestamps, ordering, precision)

Output:

- `verification.plan.md`

## How to Prompt an LLM to Produce a Safe “Allowed Differences” List

This list prevents endless debates during cutover.

```text
Create an "Allowed Differences" policy for verifying a rewrite.

Input context:
- Legacy: Python + SQLite
- Target: Rust + Postgres
- We will compare outputs from the same baseline dataset.

Output:
- A short policy with explicit examples:
  - ordering differences
  - timestamp/timezone normalization
  - float/decimal precision
  - NULL vs empty
  - eventual consistency delays
- For each allowed difference, define how to normalize before diff.
```

## Notes on Data Migration (Table Splits and Field Remapping)

When schemas change, validation needs extra structure:

- Define a mapping table: legacy PK → new PK(s)
- For split tables, define join keys and reconstruction queries
- Track derived fields: which are computed, from what inputs
- Use checksums for reconstructed “logical entities” (not just raw rows)

## Suggested Next Step

Once you have a baseline evidence pack, you can start the rewrite with a loop:

1) run baseline against legacy → capture outputs
2) run baseline against new system → capture outputs
3) diff → triage → fix

This is how you keep a rewrite safe even when you change language and storage.
