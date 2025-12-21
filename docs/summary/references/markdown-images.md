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
