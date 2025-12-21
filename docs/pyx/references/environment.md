# pyx Environment Information

Public-safe environment guidance for pyx.
This file avoids embedding machine-specific paths or package inventories.

## Runtime Detection (Recommended)

To learn the *current* environment on any machine, run:

```bash
pyx info
pyx info --json
```

`pyx info --json` includes:
- OS + shell type
- dynamically-tested shell syntax support
- env var *keys* (values hidden)
- available system commands (111 checks)

## Notes

- Do not assume tools exist. Always check `pyx info --commands` or `pyx info --json`.
- Prefer using external tools via `subprocess.run()` inside pyx scripts (not raw shell).
