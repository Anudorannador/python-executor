# Code Verification

Code verification means validating an answer against the *actual* code and installed artifacts in the current environment.
This must be evidence-based and reproducible.

## Principles

- Use MANIFEST_IO scripts to collect evidence.
- Prefer lockfiles and installed outputs over assumptions.
- Record paths/sizes of artifacts in the investigation log.

## Documentation Verification (MCP / Official Docs)

Sometimes “verify against code” is not enough:

- You may need the *intended* API behavior (official docs).
- You may need usage patterns (examples, migration notes, deprecations).
- The local environment may not contain the relevant source (e.g., remote SaaS APIs).

### When to use docs

Use documentation verification when any of these are true:

- The question is about an API contract (parameters, defaults, return shapes, errors).
- The code is generated/compiled/minified and hard to inspect locally.
- The installed version differs from what the user targets (you need to confirm the version).
- The user explicitly requests “check the docs”.

### How to verify docs (evidence-based)

Use MCP tools when available (examples):

- DeepWiki (repo-aware docs)
- Microsoft Docs (official product API references)
- Other MCP doc/search tools available in the environment

Rules:

1. **Confirm the source** (which site/repo/version). Do not guess versions.
2. **Record the exact query** you ran (tool name + query string).
3. **Capture evidence** as files via MANIFEST_IO:
   - outputs: extracted snippets, URLs, key sections, version notes
   - manifest + log paths in the investigation log
4. If docs and local code disagree, **report both** and state which one is authoritative for the user’s target version.

Recommended artifacts:

- `temp/<topic>.<run_id>.docs.json` (structured findings)
- `temp/<topic>.<run_id>.docs.txt` (human-readable notes)
- `temp/<topic>.<run_id>.manifest.json` + `temp/<topic>.<run_id>.log.txt`

## Common Targets

### Python
- `.venv/` existence and interpreter path
- Installed packages: `pip list`, `pip show <pkg>`
- Import resolution: `python -c "import pkg; print(pkg.__file__)"`

### Node.js
- `package.json` + lockfile (`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`)
- Installed modules: `node_modules/` (and `npm ls` if needed)

### Rust/Cargo
- `Cargo.toml` + `Cargo.lock`
- Build artifacts: `target/` (if present)

## Output

Always produce:
- a manifest file listing evidence outputs
- a short stdout summary
- and record everything in the investigation log
