"""Leader-summary template generation.

Creates a small set of markdown templates intended for producing
leader-friendly status updates.

This is intentionally kept independent from the Claude skill generators so it
can be invoked directly via `pyx summary`.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from .common import GenerateSummaryResult


def generate_summary_files(
    output_dir: str | Path,
    *,
    force: bool = False,
) -> GenerateSummaryResult:
    output_path = Path(output_dir)
    refs_path = output_path / "references"

    backup_dir: str | None = None
    if output_path.exists() and not force:
        backup_dir = _backup_directory(output_path)

    output_path.mkdir(parents=True, exist_ok=True)
    refs_path.mkdir(parents=True, exist_ok=True)

    files_created: list[str] = []

    skill_path = output_path / "SKILL.md"
    skill_path.write_text(_build_skill_md(), encoding="utf-8")
    files_created.append(str(skill_path.resolve()))

    template_path = refs_path / "leader-summary-template.md"
    template_path.write_text(_build_leader_summary_template_md(), encoding="utf-8")
    files_created.append(str(template_path.resolve()))

    images_path = refs_path / "markdown-images.md"
    images_path.write_text(_build_markdown_images_md(), encoding="utf-8")
    files_created.append(str(images_path.resolve()))

    return GenerateSummaryResult(
        success=True,
        output_dir=str(output_path.resolve()),
        files_created=files_created,
        backup_dir=backup_dir,
    )


def _backup_directory(path: Path) -> str | None:
    """Backup entire directory to path.bak or path.bak.N."""
    if not path.exists():
        return None

    backup_path = Path(f"{path}.bak")
    if backup_path.exists():
        i = 1
        while Path(f"{path}.bak.{i}").exists():
            i += 1
        backup_path = Path(f"{path}.bak.{i}")

    shutil.move(str(path), str(backup_path))
    return str(backup_path)


def _build_skill_md() -> str:
    lines: list[str] = []

    lines.append("---")
    lines.append("name: summary")
    lines.append(
        'description: "Create leader-ready status updates (one-pagers) with clear highlights, risks, next steps, and optional images."'
    )
    lines.append("version: 0.1.0")
    lines.append("---")
    lines.append("")

    lines.append("# Summary")
    lines.append("")
    lines.append("Generate concise, leader-friendly status summaries.")
    lines.append("")

    lines.append("## Output")
    lines.append("")
    lines.append("Use the template in `references/leader-summary-template.md`.")
    lines.append("")

    lines.append("## Rules")
    lines.append("")
    lines.append("- Keep it scannable: short sections + bullet points")
    lines.append("- Lead with outcomes and impact")
    lines.append("- Call out risks clearly with owners and mitigations")
    lines.append("- Include links to evidence (PRs, dashboards, logs)")
    lines.append("- If images are included, prefer small screenshots with captions")
    lines.append("")

    lines.append("## Images")
    lines.append("")
    lines.append("See `references/markdown-images.md` for safe, portable markdown image linking.")
    lines.append("")

    return "\n".join(lines)


def _build_leader_summary_template_md() -> str:
    lines: list[str] = []

    lines.append("# Leader Summary")
    lines.append("")
    lines.append("Date: <YYYY-MM-DD>")
    lines.append("Owner: <name/team>")
    lines.append("Audience: <e.g. Eng leadership / Product>")
    lines.append("")

    lines.append("## One-liner")
    lines.append("")
    lines.append("<What happened / what changed / why it matters. 1–2 sentences.>")
    lines.append("")

    lines.append("## Highlights")
    lines.append("")
    lines.append("- <ship/blocker resolved/decision made>")
    lines.append("- <metric movement or customer impact>")
    lines.append("- <notable risk retired>")
    lines.append("")

    lines.append("## Progress")
    lines.append("")
    lines.append("- Status: <green/yellow/red>")
    lines.append("- What’s done: <2–5 bullets>")
    lines.append("- What’s in flight: <2–5 bullets>")
    lines.append("")

    lines.append("## Risks / Blockers")
    lines.append("")
    lines.append("- <risk>: <impact> — Owner: <name> — Mitigation: <plan> — ETA: <date>")
    lines.append("")

    lines.append("## Next 7 Days")
    lines.append("")
    lines.append("- <next concrete deliverable>")
    lines.append("- <decision needed>")
    lines.append("- <dependency to unblock>")
    lines.append("")

    lines.append("## Links")
    lines.append("")
    lines.append("- PRs: <url>")
    lines.append("- Dashboard: <url>")
    lines.append("- Runbook / doc: <url>")
    lines.append("")

    lines.append("## Images (optional)")
    lines.append("")
    lines.append("Use images only when they add clarity (e.g., graph, screenshot of UI change, error diff).")
    lines.append("")
    lines.append("Example:")
    lines.append("")
    lines.append("```md")
    lines.append("![Latency p95 improved after rollout](./images/latency-p95.png)")
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


def _build_markdown_images_md() -> str:
    lines: list[str] = []

    lines.append("# Markdown Images")
    lines.append("")
    lines.append("## Syntax")
    lines.append("")
    lines.append("```md")
    lines.append("![alt text](path-or-url)")
    lines.append("```")
    lines.append("")

    lines.append("## Recommended: relative paths")
    lines.append("")
    lines.append("Keep images near the markdown file so links remain portable.")
    lines.append("")
    lines.append("Example directory:")
    lines.append("")
    lines.append("```text")
    lines.append("docs/summary/")
    lines.append("├── report.md")
    lines.append("└── images/")
    lines.append("    └── chart.png")
    lines.append("```")
    lines.append("")

    lines.append("Example usage:")
    lines.append("")
    lines.append("```md")
    lines.append("![Chart](./images/chart.png)")
    lines.append("```")
    lines.append("")

    lines.append("## Tips")
    lines.append("")
    lines.append("- Use short, descriptive filenames (e.g., `error-rate.png`)")
    lines.append("- Prefer small images; crop to the relevant area")
    lines.append("- Always include a meaningful caption in the alt text")
    lines.append("")

    return "\n".join(lines)
