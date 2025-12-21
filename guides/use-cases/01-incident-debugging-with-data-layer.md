# Use Case 1: Incident Debugging With Data-Layer Access (DB/Redis/Kafka)

## Scenario

You maintain an internal system used by other teammates. When something goes wrong, you typically face situations like:

- A teammate reports a bug or incorrect data produced by the system.
- You need to debug quickly by connecting to the data layer (MySQL, Redis, Kafka).
- Access is via TCP forwarding, so the actual connections are always `localhost:<port>`.
- After restoring correctness, you must explain the cause to the teammate and write a leader-facing postmortem.
- You also want to extract reusable knowledge (“learn”) so future investigations do not start from zero.

## How this guide helps

This guide is **prompt-first**: it shows how to instruct an LLM to use `python-executor (pyx)` correctly to produce evidence, logs, summaries, and learn outputs.

- A teammate reports a bug or incorrect data.
- You need to investigate by connecting to the data layer (database, Redis, Kafka).
- Your access is via TCP forwarding, so everything is `localhost:<port>`.
- You must produce (a) an answer for the teammate + a leader-ready write-up and (b) reusable “learn” outputs so the next incident is faster.

## What “Good” Looks Like (Deliverables)

When done, you should have:

1) **Evidence (MANIFEST_IO artifacts)** for each major check
   - script + input JSON + manifest + log + output files

2) **An investigation log**
   - `temp/<topic>.<run_id>.inspect.md` with links to evidence files

3) **Two summaries**
   - a teammate-facing explanation (what happened, workaround, next steps)
   - a leader-facing postmortem (impact, root cause, detection gap, prevention actions)

4) **A learn extraction plan**
   - what becomes project-specific knowledge vs what becomes global reusable templates

## Copy/Paste Prompt Template (Incident Investigation)

Paste this into your LLM chat at the start of an investigation.

```text
You are my incident investigation assistant.

Hard requirements:
- Use python-executor (pyx) and MANIFEST_IO for any computation or lookup.
- Do NOT guess data-layer connection details.
- My data-layer access is via TCP forwarding, so all endpoints are localhost ports.
- Prefer file-based evidence over chat explanations: write outputs to files and reference them.

Workflow:
1) Ask me for the minimum inputs you need (environment name, entity IDs, time window).
2) Propose an investigation plan as a checklist.
3) For each step, create a MANIFEST_IO task:
   - script: temp/<task>.py
   - input:  temp/<task>.input.json
   - outputs: write JSON/CSV/TXT files
   - manifest + log produced via `pyx run`
4) Maintain an investigation log:
   - temp/<topic>.<run_id>.inspect.md
   - include hypotheses, steps taken, and links to manifests/logs/outputs.
5) End with two write-ups:
   - teammate summary (short)
   - leader postmortem (root cause + prevention actions with owners/dates)

Connection policy:
- Read all connection details from env vars only.
- If multiple environments exist, list the candidate env var names and ask me to confirm which ones to use.

Start by asking me for:
- Incident title/topic
- Environment (e.g., PROD/STAGING)
- Entity identifiers (user_id/order_id/etc.)
- Time window + timezone assumption
```

## Inputs You Should Provide to the LLM

At minimum:

- **Environment label** (e.g. `PROD`, `STAGING`)
- **IDs** involved (user/order/payment/etc.)
- **Time window** (start/end + timezone policy)
- **Symptoms** (what is wrong, expected vs actual)

Optional but high value:

- A screenshot or example payload
- The code entrypoint/module you suspect

## Data-Layer Env Vars (localhost tunnels)

Do not hardcode secrets into files. Read from environment variables.

If your org standardizes on URL-style env vars, use:

- `MYSQL_<ENV>_URL=mysql://user:pass@127.0.0.1:<port>/<db>`
- `REDIS_<ENV>_URL=redis://:pass@127.0.0.1:<port>/<db>`
- `KAFKA_<ENV>_BROKERS=127.0.0.1:<port>` (or comma-separated)

Where `<ENV>` is `DEV`, `STAGING`, `PROD`, etc.

## How to “Teach” the LLM to Avoid Common Failure Modes

### Require fingerprints first

In your prompt, explicitly require “fingerprint” checks to avoid wrong-environment mistakes:

- DB fingerprint (db name/user/version/time)
- Redis fingerprint (`INFO server`, keyspace summary)
- Kafka fingerprint (cluster/broker metadata + relevant topic list)

Each fingerprint step should be its own MANIFEST_IO run with outputs written to files.

### Require diff-first outputs

Tell the LLM to produce diffs, not just raw dumps:

- DB value vs cache value diff JSON
- expected vs actual CSV
- Kafka offsets/lag summaries

### Require explicit evidence links

In the investigation log and final summaries, require links to:

- manifests (what ran)
- logs (stdout/stderr)
- output files (results)

## Recommended Investigation Ordering (Tell the LLM)

For “data is wrong” incidents, instruct:

1) Database (source of truth)
2) Redis (cache/derived view)
3) Kafka (async pipeline / eventual consistency)

Each step should be a small, single-purpose `pyx run` task.

## Suggested File Conventions (Make learning easy)

Standardize input/output file naming so later learn extraction is painless:

- Inputs
  - `temp/<task>.input.json` includes `time_window`, `entity_ids`, `notes`
- Outputs
  - `fingerprint.*.json`
  - `db_rows.*.csv`
  - `redis_value.*.json`
  - `kafka_offsets.*.json`
  - `diff.*.json`

## After the Incident: Summary + Learn

In your prompt, explicitly require two outputs:

1) Teammate summary (short): what happened, workaround, ETA, data correction plan
2) Leader postmortem: impact, root cause, detection gap, prevention actions (owners + due dates)

Then require a learn handoff:

- What becomes project-specific (names, tables, topics, internal semantics)
- What becomes global template knowledge (generic workflow, checklists, placeholders)

See Use Case 2 for the project-vs-global template policy.
