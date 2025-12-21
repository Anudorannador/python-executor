# summary

This reference provides a leader-summary template and image linking guidance.

## Template

# Leader Summary

Date: <YYYY-MM-DD>
Owner: <name/team>
Audience: <e.g. Eng leadership / Product>

## One-liner

<What happened / what changed / why it matters. 1–2 sentences.>

## Highlights

- <ship/blocker resolved/decision made>
- <metric movement or customer impact>
- <notable risk retired>

## Progress

- Status: <green/yellow/red>
- What’s done: <2–5 bullets>
- What’s in flight: <2–5 bullets>

## Risks / Blockers

- <risk>: <impact> — Owner: <name> — Mitigation: <plan> — ETA: <date>

## Next 7 Days

- <next concrete deliverable>
- <decision needed>
- <dependency to unblock>

## Links

- PRs: <url>
- Dashboard: <url>
- Runbook / doc: <url>

## Images (optional)

Use images only when they add clarity (e.g., graph, screenshot of UI change, error diff).

Example:

```md
![Latency p95 improved after rollout](./images/latency-p95.png)
```

## Images

# Markdown Images

## Syntax

```md
![alt text](path-or-url)
```

## Recommended: relative paths

Keep images near the markdown file so links remain portable.

Example directory:

```text
docs/summary/
├── report.md
└── images/
    └── chart.png
```

Example usage:

```md
![Chart](./images/chart.png)
```

## Tips

- Use short, descriptive filenames (e.g., `error-rate.png`)
- Prefer small images; crop to the relevant area
- Always include a meaningful caption in the alt text
