# learn skill

Extract reusable skills from any source: task files, chat history, or any data-producing operation.

## Trigger

Activate when user says:
- "learn skill"
- "save as skill"
- "distill skill"
- "extract skill"

## Input Sources

Skills can be extracted from:
- `temp/` task files (scripts, manifests, logs)
- Chat conversation history
- Any operation that produced data/code
- User-provided code snippets or workflows

## Output Format: Claude SKILL Standard

```
<skill_name>/
├── SKILL.md           # Core instructions (required)
└── references/        # Optional reference docs
    └── <detail>.md
```

## Storage Locations

| Location | Path | Use Case |
|----------|------|----------|
| Project | `docs/<skill_name>/SKILL.md` | Project-specific skills |
| Global | `~/.claude/skills/<skill_name>/SKILL.md` | Cross-project skills |

## Workflow

```
1. Identify source (files / chat / user input)
2. Summarize content (token-efficient)
3. Scan existing skills (headers ONLY)
4. Recommend action: create / merge / overwrite
5. Generate SKILL markdown
6. **USER CONFIRMS** -> then save
```

## Summarize Content (Token-Efficient)

**CRITICAL: DO NOT read full files. Extract summaries only.**

For files:
- Script: first 30 lines + last 10 lines
- JSON: keys only, truncate values
- Manifest: paths and sizes only
- Log: first 10 lines only

## Scan Existing Skills (Headers Only)

**CRITICAL: DO NOT read full SKILL files. Token explosion risk.**

```bash
# Project skills
ls -d docs/*/SKILL.md 2>/dev/null || echo "(none)"

# Global skills (Unix)
ls -d ~/.claude/skills/*/SKILL.md 2>/dev/null || echo "(none)"

# Global skills (Windows)
dir /b "%USERPROFILE%\.claude\skills\*\SKILL.md" 2>nul || echo "(none)"
```

For each SKILL.md, read ONLY lines 1-20 to extract name and description.

## Recommend Action

| Mode | When to Use |
|------|-------------|
| `create` | No similar skill exists |
| `merge` | Similar skill exists, add as variant/section |
| `overwrite` | Replace existing skill entirely |

**If user does not specify mode, LLM decides and proposes.**

## Preview Before Save

**ALWAYS show generated content to user before saving.**

## User Confirmation Required

**NEVER save without explicit user confirmation.**

- `create`: Show preview, ask confirm
- `merge`: Show diff, ask confirm
- `overwrite`: Show warning, ask confirm

## Related

- [MANIFEST_IO Mode](manifest-io.md) - File-first workflow for task execution
