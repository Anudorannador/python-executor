# Code Verification

Code verification means validating an answer against the *actual* code and installed artifacts in the current environment.
This must be evidence-based and reproducible.

## Principles

- Use MANIFEST_IO scripts to collect evidence.
- Prefer lockfiles and installed outputs over assumptions.
- Record paths/sizes of artifacts in the investigation log.

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
