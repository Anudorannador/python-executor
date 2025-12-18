# pyx learn skill

Extract reusable skills from recent MANIFEST_IO task executions.

## Trigger

Activate when user says:

- "pyx learn skill"
- "learn this as skill"
- "save as skill"
- "distill skill"

## Workflow Overview

```
1. Scan temp/ for recent tasks
2. Summarize task (NOT full content)
3. Scan existing recipes (headers only)
4. Recommend: new / merge / skip
5. Generate recipe markdown
6. User confirms → save to project or global
```

## Step 1: Find Recent Task Files

```bash
# List recent files in temp/
pyx run --file "temp/list_recent.py"
```

Look for file patterns:

- `temp/<task>.py` - Script
- `temp/<task>.input.json` - Input
- `temp/<task>.<run_id>.manifest.json` - Manifest
- `temp/<task>.<run_id>.log.txt` - Log

**Important**: If multiple tasks exist, ask user which one to learn.

## Step 2: Summarize Task (Token-Efficient)

**DO NOT read full file content into context.**

Instead, extract summary:

```python
# Read script: first 30 lines + last 10 lines
# Read input.json: keys only, not values
# Read manifest: paths and sizes only
# Read log: first 10 lines only
```

Build mental summary:

- **Purpose**: What does this script do?
- **Input**: What data does it need?
- **Output**: What files does it produce?
- **Dependencies**: What packages does it use?

## Step 3: Scan Existing Skills (Headers Only)

**CRITICAL: DO NOT read full recipe files. Token explosion risk.**

### 3.1 List Recipe Files

```bash
# Project recipes
ls docs/pyx/recipes/*.md 2>/dev/null || echo "(none)"

# Global recipes (Unix)
ls ~/.pyx/recipes/*.md 2>/dev/null || echo "(none)"

# Global recipes (Windows)
dir "%USERPROFILE%\.pyx\recipes\*.md" 2>nul || echo "(none)"
```

### 3.2 Extract Headers Only

For each `.md` file, read ONLY lines 1-15 to extract:

- Title (first `#` line)
- Tags (from frontmatter or first paragraph)
- Brief description

### 3.3 Build Index

Create mental index:

| File | Title | Tags |
|------|-------|------|
| api_fetch.md | API Data Fetcher | api, http, json |
| db_query.md | Database Query | mysql, query |
| file_proc.md | File Processor | csv, excel |

## Step 4: Recommend Action

Based on task summary and existing index:

| Condition | Recommendation |
|-----------|----------------|
| No similar recipe exists | **NEW**: Create new recipe |
| Similar recipe exists (70%+ overlap) | **MERGE**: Add variant to existing |
| Nearly identical recipe exists | **SKIP**: Already covered |

Present recommendation to user:

```
Based on your task "Fetch API data with pagination":

Existing recipes scanned: 5
Similar recipe found: api_fetch.md (API Data Fetcher)

Recommendation: MERGE
- Add pagination variant to existing api_fetch.md

Options:
1. Merge to existing recipe
2. Create as new recipe anyway
3. Save to global recipes
4. Cancel
```

## Step 5: Generate Recipe

### Recipe Format

```markdown
---
name: <snake_case_name>
tags: [tag1, tag2, tag3]
created: YYYY-MM-DD
source: temp/<task>.py
---

# <Recipe Title>

## When to Use

- Scenario 1
- Scenario 2

## Quick Start

1. Create input file...
2. Run command...

## Code Template

\```python
# Distilled, reusable code
# Remove hardcoded values
# Add configuration parameters
\```

## Input Schema

\```json
{
  "param1": "description",
  "param2": "description"
}
\```

## Notes

- Important consideration 1
- Common pitfall to avoid
```

### Distillation Rules

When generating code template:

1. **Parameterize** - Replace hardcoded values with config
2. **Generalize** - Remove task-specific logic
3. **Document** - Add inline comments
4. **Simplify** - Remove debug/temporary code

## Step 6: Save Recipe

### Project Recipes

```bash
# Ensure directory exists
pyx ensure-temp --dir "docs/pyx/recipes"

# Write recipe file
# File: docs/pyx/recipes/<name>.md
```

### Global Recipes

```bash
# Unix/macOS
mkdir -p ~/.pyx/recipes

# Windows
mkdir "%USERPROFILE%\.pyx\recipes" 2>nul

# Write recipe file
# File: ~/.pyx/recipes/<name>.md (Unix)
# File: %USERPROFILE%\.pyx\recipes\<name>.md (Windows)
```

## Example Session

**User**: pyx learn skill

**Assistant**:

```
Scanning temp/ for recent tasks...

Found:
1. fetch_prices.py (2 min ago) - with manifest
2. convert_excel.py (1 hour ago) - with manifest

Which task to learn? [1/2]: 
```

**User**: 1

**Assistant**:

```
Analyzing fetch_prices.py...

Summary:
- Purpose: Fetch cryptocurrency prices from exchange API
- Input: list of symbols, timeframe
- Output: JSON with OHLCV data
- Packages: ccxt, pandas

Scanning existing recipes...
- Project: 3 recipes
- Global: 2 recipes

No similar recipe found.

Recommendation: NEW
Create new recipe: crypto_price_fetcher.md

Generate recipe? [y/n]:
```

**User**: y

**Assistant**: (generates recipe markdown)

```
Save to:
1. Project (docs/pyx/recipes/)
2. Global (~/.pyx/recipes/)
3. Print only (don't save)
```

## Related

- [MANIFEST_IO Mode](manifest-io.md) - The execution workflow that produces learnable tasks
- [Commands Reference](commands.md) - pyx CLI commands
