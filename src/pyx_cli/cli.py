"""
CLI interface for python-executor.
Provides command line access to the executor functions.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from datetime import datetime
from pathlib import Path
import shutil
import site
import importlib
import importlib.metadata
import re
from typing import NoReturn

from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Confirm
from rich.syntax import Syntax

# Load .env files before importing pyx_core (which may use env vars)
# Priority (later overrides earlier):
# 1. User config: ~/.config/pyx/.env (Unix) or %APPDATA%\pyx\.env (Windows)
# 2. Local .env from cwd
if sys.platform == "win32":
    _USER_CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home())) / "pyx"
else:
    _USER_CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "pyx"
_USER_ENV_PATH = _USER_CONFIG_DIR / ".env"

if _USER_ENV_PATH.exists():
    load_dotenv(_USER_ENV_PATH, override=False)
# Local .env from cwd (overrides user config)
load_dotenv(override=True)

from pyx_core import (  # noqa: E402
    __version__,
    run_code,
    run_file,
    run_async_code,
    add_package,
    ensure_temp,
    get_environment_info,
    format_environment_info,
    get_uv_env,
    generate_pyx_instructions,
    generate_shell_instructions,
    generate_skill_files,
    save_with_backup,
    _generate_skill_md,
    _generate_inspect_skill_md,
)

console = Console()


def _redact_markdown(markdown: str) -> str:
    """Redact common local/PII paths and credential-like URLs from generated docs.

    Goal: keep the document useful while removing user-specific filesystem details.
    """
    redacted = markdown

    # Redact the current user's home directory while preserving Windows-ness.
    try:
        home = str(Path.home())
        if home:
            redacted = redacted.replace(home, r"C:\Users\<REDACTED_USER>")
    except Exception:
        pass

    # Redact VS Code profile ids inside typical prompts paths.
    # Example: ...\profiles\-7c411965\prompts\...
    redacted = re.sub(r"(\\profiles\\)[^\\]+(\\prompts\\)", r"\1<REDACTED_PROFILE>\2", redacted, flags=re.IGNORECASE)

    # Redact credential-like URLs if they ever appear.
    redacted = re.sub(r"\b(mysql\+pymysql|mysql|postgres|redis)://[^\s]+", r"<REDACTED_URL>", redacted, flags=re.IGNORECASE)

    return redacted


def _append_help_section(lines: list[str], title: str, help_text: str) -> None:
    lines.append(title)
    lines.append("")
    lines.append("```text")
    lines.extend(help_text.rstrip("\n").splitlines())
    lines.append("```")
    lines.append("")


def _iter_subparsers(parser: argparse.ArgumentParser) -> list[argparse._SubParsersAction]:
    return [
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    ]


def _collect_unique_parsers(subparsers: argparse._SubParsersAction) -> list[tuple[str, list[str], argparse.ArgumentParser]]:
    # argparse stores aliases as additional keys in .choices.
    # Deduplicate by parser identity, while keeping all names for that parser.
    by_id: dict[int, tuple[list[str], argparse.ArgumentParser]] = {}
    for name, subparser in sorted(subparsers.choices.items()):
        key = id(subparser)
        if key not in by_id:
            by_id[key] = ([name], subparser)
        else:
            by_id[key][0].append(name)

    items: list[tuple[str, list[str], argparse.ArgumentParser]] = []
    for names, subparser in by_id.values():
        primary = sorted(names)[0]
        items.append((primary, sorted(names), subparser))
    items.sort(key=lambda x: x[0])
    return items


def _generate_pyx_help_instructions_markdown(parser: argparse.ArgumentParser) -> str:
    lines: list[str] = []
    lines.append("---")
    lines.append('applyTo: "**"')
    lines.append('name: "pyx-help-instructions"')
    lines.append('description: "Auto-generated pyx CLI help outputs (pyx --help and subcommands)."')
    lines.append("---")
    lines.append("")
    lines.append("# pyx Help Output")
    lines.append("")
    lines.append("This file captures the output of `pyx --help` and all subcommand `--help` outputs.")
    lines.append("")

    _append_help_section(lines, "## `pyx --help`", parser.format_help())

    top_subparsers = _iter_subparsers(parser)
    if not top_subparsers:
        return "\n".join(lines)

    top = top_subparsers[0]
    for primary, names, subparser in _collect_unique_parsers(top):
        alias_note = "" if names == [primary] else f" (aliases: {', '.join(n for n in names if n != primary)})"
        _append_help_section(lines, f"## `pyx {primary} --help`{alias_note}", subparser.format_help())

        nested_subparsers = _iter_subparsers(subparser)
        if not nested_subparsers:
            continue

        nested = nested_subparsers[0]
        for sub_primary, sub_names, nested_parser in _collect_unique_parsers(nested):
            nested_alias_note = "" if sub_names == [sub_primary] else f" (aliases: {', '.join(n for n in sub_names if n != sub_primary)})"
            _append_help_section(
                lines,
                f"### `pyx {primary} {sub_primary} --help`{nested_alias_note}",
                nested_parser.format_help(),
            )

    return "\n".join(lines)


def _strip_frontmatter(markdown: str) -> str:
    """Remove a leading YAML frontmatter block if present."""
    lines = markdown.splitlines()
    if not lines or lines[0].strip() != "---":
        return markdown
    # Find closing '---'
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            rest = lines[i + 1 :]
            # Drop a single leading blank line after frontmatter
            if rest and rest[0].strip() == "":
                rest = rest[1:]
            return "\n".join(rest)
    return markdown


def _extract_from_heading(markdown: str, heading_prefix: str) -> str:
    """Return markdown starting from the first line that begins with heading_prefix.

    If not found, returns the original markdown.
    """
    lines = markdown.splitlines()
    for i, line in enumerate(lines):
        if line.startswith(heading_prefix):
            return "\n".join(lines[i:])
    return markdown


def _build_combined_instructions_markdown(
    parser: argparse.ArgumentParser,
    style: str,
) -> tuple[str, dict[str, object]]:
    pyx_result = generate_pyx_instructions(show_progress=True, style=style)
    if not pyx_result.success:
        raise RuntimeError(pyx_result.error or "Failed to generate pyx-usage instructions")

    shell_result = generate_shell_instructions(show_progress=True)
    if not shell_result.success:
        raise RuntimeError(shell_result.error or "Failed to generate shell-usage instructions")

    help_md = _generate_pyx_help_instructions_markdown(parser)

    # Avoid duplication: shell-usage repeats environment + env vars + commands.
    # Keep only the shell-specific guidance section(s).
    shell_body = _strip_frontmatter(shell_result.markdown)
    shell_body = _extract_from_heading(shell_body, "## Shell Overview")

    def _format_paths_section() -> str:
        parts: list[str] = []
        parts.append("## pyx installation")
        parts.append("")
        parts.append("### Paths")
        parts.append("")

        pyx_bin = shutil.which("pyx")
        pyx_mcp_bin = shutil.which("pyx-mcp")

        parts.append("```text")
        parts.append(f"pyx executable: {pyx_bin or '<not found on PATH>'}")
        parts.append(f"pyx-mcp executable: {pyx_mcp_bin or '<not found on PATH>'}")
        parts.append(f"pyx Python (sys.executable): {sys.executable}")
        parts.append("```")
        parts.append("")

        parts.append("### Module locations")
        parts.append("")
        module_names = ["pyx_core", "pyx_cli", "pyx_mcp"]
        parts.append("```text")
        for name in module_names:
            try:
                mod = importlib.import_module(name)
                mod_file = getattr(mod, "__file__", None)
                parts.append(f"{name}.__file__: {mod_file}")
            except Exception as e:
                parts.append(f"{name}.__file__: <error: {e}>")
        parts.append("```")
        parts.append("")

        parts.append("### Python site-packages")
        parts.append("")
        parts.append("```text")
        try:
            for p in site.getsitepackages():
                parts.append(f"site-packages: {p}")
        except Exception as e:
            parts.append(f"site.getsitepackages(): <error: {e}>")
        try:
            parts.append(f"user-site: {site.getusersitepackages()}")
        except Exception as e:
            parts.append(f"site.getusersitepackages(): <error: {e}>")
        parts.append("```")
        parts.append("")

        # Best-effort repo root guess (useful for editable installs)
        parts.append("### Quick update / reinstall")
        parts.append("")
        repo_root_guess: str | None = None
        try:
            cli_mod = importlib.import_module("pyx_cli")
            cli_file = Path(getattr(cli_mod, "__file__", "")).resolve()
            # If installed from source, the module path often looks like: <repo>/src/pyx_cli/__init__.py
            if "src" in cli_file.parts:
                src_index = cli_file.parts.index("src")
                repo_root_guess = str(Path(*cli_file.parts[:src_index]).resolve())
        except Exception:
            repo_root_guess = None

        parts.append("If you are developing from the source repo (editable install), update/reinstall from the repo root:")
        parts.append("")
        parts.append("```bash")
        if repo_root_guess:
            parts.append(f"# Repo root (best guess): {repo_root_guess}")
        parts.append("# Reinstall pyx in editable mode")
        parts.append('uv tool install -e ".[full]"')
        parts.append("```")
        parts.append("")
        parts.append("Notes:")
        parts.append("")
        parts.append("- If `pyx_cli.__file__` points into `site-packages`, you are likely using a non-editable install.")
        parts.append("- To switch to editable development, clone the repo and run the command above from the repo root.")
        parts.append("")

        return "\n".join(parts)

    def _format_installed_packages_section() -> str:
        parts: list[str] = []
        parts.append("## Installed Python packages (pyx environment)")
        parts.append("")
        try:
            dists = list(importlib.metadata.distributions())
            items: list[tuple[str, str]] = []
            for d in dists:
                name = (d.metadata.get("Name") or d.metadata.get("Summary") or "").strip() or d.metadata.get("name")
                if not name:
                    name = getattr(d, "name", None) or "<unknown>"
                version = getattr(d, "version", None) or ""
                items.append((str(name), str(version)))
            items.sort(key=lambda x: x[0].lower())

            parts.append(f"Total distributions: {len(items)}")
            parts.append("")
            parts.append("```text")
            for name, version in items:
                if version:
                    parts.append(f"{name}=={version}")
                else:
                    parts.append(name)
            parts.append("```")
        except Exception as e:
            parts.append(f"Failed to enumerate packages: {e}")
        parts.append("")
        return "\n".join(parts)

    combined: list[str] = []
    combined.append("---")
    combined.append('applyTo: "**"')
    combined.append('name: "pyx-instructions"')
    combined.append('description: "Auto-generated combined instructions (pyx-usage + shell-usage + pyx-help)."')
    combined.append("---")
    combined.append("")
    combined.append("# pyx Instructions")
    combined.append("")
    combined.append("This file combines:")
    combined.append("")
    combined.append("- pyx-usage (file-first + output explosion control)")
    combined.append("- shell-usage (shell syntax guidance)")
    combined.append("- pyx-help (CLI help output snapshot)")
    combined.append("")
    combined.append("---")
    combined.append("")
    combined.append("## pyx-usage")
    combined.append("")
    combined.append(_strip_frontmatter(pyx_result.markdown))
    combined.append("")

    combined.append("---")
    combined.append("")
    combined.append(_format_paths_section())
    combined.append("")

    combined.append("---")
    combined.append("")
    combined.append(_format_installed_packages_section())
    combined.append("")

    combined.append("---")
    combined.append("")
    combined.append("## shell-usage")
    combined.append("")
    combined.append(shell_body)
    combined.append("")
    combined.append("---")
    combined.append("")
    combined.append("## pyx-help")
    combined.append("")
    combined.append(_strip_frontmatter(help_md))
    combined.append("")

    summary: dict[str, object] = {
        "os": pyx_result.raw_info.os_name,
        "shell": pyx_result.raw_info.shell_type,
        "python_version": pyx_result.raw_info.python_version,
        "pyx_version": pyx_result.raw_info.pyx_version,
        "syntax_patterns_count": len(pyx_result.raw_info.syntax_support),
        "env_variables_count": len(pyx_result.env_keys_with_usage),
        "available_commands_count": sum(1 for d in pyx_result.raw_info.commands.values() if d["available"]),
        "total_commands_checked": len(pyx_result.raw_info.commands),
    }

    return "\n".join(combined), summary


def build_parser() -> tuple[argparse.ArgumentParser, argparse.ArgumentParser]:
    parser = argparse.ArgumentParser(
        prog="pyx",
        description="A cross-platform Python code executor that avoids shell-specific issues.",
    )
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # run command
    run_parser = subparsers.add_parser("run", help="Run Python code or a script file")
    run_parser.add_argument("--cwd", type=str, help="Change to this directory before execution")
    run_parser.add_argument("--timeout", "-t", type=float, help="Maximum execution time in seconds")
    run_parser.add_argument("--async", dest="is_async", action="store_true", help="Execute as async code (supports await)")
    run_parser.add_argument(
        "--input-path",
        type=str,
        help="Optional path to a JSON input file. Exposed to the script via env var PYX_INPUT_PATH.",
    )
    run_parser.add_argument(
        "--output-path",
        type=str,
        help="Optional manifest path (Strategy A). If not provided, pyx writes <base>.<run_id>.manifest.json into the resolved output directory.",
    )
    run_parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory used for auto-generated outputs (default: temp). If --input-path is provided, its directory is used by default.",
    )
    run_group = run_parser.add_mutually_exclusive_group(required=True)
    run_group.add_argument("--code", "-c", type=str, help="Inline Python code to execute")
    run_group.add_argument("--file", "-f", type=str, help="Path to a Python script file. Use -- to pass args to script.")
    run_group.add_argument("--base64", "-b", type=str, help="Base64-encoded Python code to execute (avoids shell escaping issues)")
    run_parser.add_argument("--yes", "-y", action="store_true", help="(Deprecated) Not allowed with --base64; kept for compatibility")
    run_parser.add_argument("script_args", nargs="*", help="Arguments to pass to the script (after --)")

    # add command
    add_parser = subparsers.add_parser("add", help="Install a Python package")
    add_parser.add_argument("--package", "-p", type=str, required=True, help="Package name to install")

    # ensure-temp command
    ensure_parser = subparsers.add_parser("ensure-temp", help="Ensure ./temp/ directory exists")
    ensure_parser.add_argument("--dir", "-d", type=str, default="temp", help="Directory to create (default: temp)")

    # info command (replaces list-env)
    info_parser = subparsers.add_parser("info", help="Show environment information (system, shell syntax, env keys, commands)")
    info_parser.add_argument("--system", action="store_true", help="Show only system info")
    info_parser.add_argument("--syntax", action="store_true", help="Show only shell syntax")
    info_parser.add_argument("--env", action="store_true", help="Show only environment keys")
    info_parser.add_argument("--commands", action="store_true", help="Show only available commands")
    info_parser.add_argument("--json", dest="as_json", action="store_true", help="Output as JSON")

    # python command
    python_parser = subparsers.add_parser(
        "python",
        help="Launch the pyx Python interpreter (interactive REPL by default)",
    )
    python_parser.add_argument(
        "python_args",
        nargs=argparse.REMAINDER,
        help="Arguments to pass through to the Python interpreter (e.g. -c, -m).",
    )

    # generate-instructions command (alias: gi)
    gen_parser = subparsers.add_parser(
        "generate-instructions",
        aliases=["gi"],
        help="Generate a single combined LLM instructions markdown file from environment info",
    )

    default_output = os.environ.get("PYX_INSTRUCTIONS_PATH", "./docs/pyx.instructions.md")
    default_style = os.environ.get("PYX_PYX_INSTRUCTIONS_STYLE", "file")
    gen_parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=default_output,
        help=f"Output path (default: $PYX_INSTRUCTIONS_PATH or {default_output})",
    )
    gen_parser.add_argument(
        "--style",
        type=str,
        choices=["file", "base64"],
        default=default_style if default_style in ("file", "base64") else "file",
        help="pyx-usage section style: 'file' (recommended) or 'base64' (legacy).",
    )
    gen_parser.add_argument("--ask", action="store_true", help="Ask before replacing existing file (default: auto-backup)")
    gen_parser.add_argument("--force", action="store_true", help="Overwrite without backup")
    gen_parser.add_argument("--print", dest="print_only", action="store_true", help="Print markdown to stdout instead of saving")

    # generate-skill command (alias: gs)
    skill_parser = subparsers.add_parser(
        "generate-skill",
        aliases=["gs"],
        help="Generate Claude skill files (SKILL.md + references/) for pyx",
    )
    default_skill_output = os.environ.get("PYX_SKILL_PATH", "./docs/pyx")
    skill_parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default=default_skill_output,
        help=f"Output directory (default: $PYX_SKILL_PATH or {default_skill_output})",
    )
    skill_parser.add_argument("--force", action="store_true", help="Overwrite without backup")
    skill_parser.add_argument("--print", dest="print_only", action="store_true", help="Print SKILL.md to stdout instead of saving")
    skill_parser.add_argument(
        "--skill",
        type=str,
        choices=["pyx", "inspect", "summary", "all"],
        default="pyx",
        help="Which skill template to generate (default: pyx). Use 'all' to generate pyx + inspect + summary.",
    )
    default_privacy = os.environ.get("PYX_SKILL_PRIVACY", "public")
    skill_parser.add_argument(
        "--privacy",
        type=str,
        choices=["public", "local"],
        default=default_privacy if default_privacy in ("public", "local") else "public",
        help="Skill output privacy mode. 'public' avoids machine-specific paths; 'local' includes details (may contain absolute paths).",
    )

    return parser, gen_parser


def main() -> NoReturn | None:
    """Main CLI entry point"""
    parser, gen_parser = build_parser()

    args = parser.parse_args()

    if args.command == "run":
        def _resolve_base_name() -> str:
            if getattr(args, "file", None):
                return Path(args.file).stem
            if getattr(args, "code", None):
                return "inline"
            if getattr(args, "base64", None):
                return "base64"
            return "run"

        def _resolve_output_dir() -> Path:
            configured = getattr(args, "output_dir", None)
            if configured:
                return Path(configured)

            input_path = getattr(args, "input_path", None)
            if input_path:
                return Path(input_path).resolve().parent

            file_path = getattr(args, "file", None)
            if file_path:
                return Path(file_path).resolve().parent

            return Path("temp")

        def _resolve_manifest_path(output_dir: Path, base: str, run_id: str) -> Path:
            configured = getattr(args, "output_path", None)
            if configured:
                return Path(configured)
            return output_dir / f"{base}.{run_id}.manifest.json"

        def _resolve_log_path(output_dir: Path, base: str, run_id: str) -> Path:
            return output_dir / f"{base}.{run_id}.log.txt"

        def _ensure_minimal_manifest(manifest_path: Path, *, run_id: str, base: str, log_path: Path, success: bool) -> None:
            if manifest_path.exists():
                return

            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            input_path = getattr(args, "input_path", None)

            payload: dict[str, object] = {
                "run_id": run_id,
                "success": success,
                "output_dir": str(manifest_path.parent.resolve()),
                "input_path": str(Path(input_path).resolve()) if input_path else None,
                "outputs": [
                    {
                        "path": str(Path(log_path).resolve()),
                        "role": "log",
                        "category": "stdout_stderr",
                        "format": "text",
                    }
                ],
            }
            manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        def _print_manifest_and_log_summary(manifest_path: Path, log_path: Path) -> None:
            try:
                manifest_size = manifest_path.stat().st_size
            except OSError:
                manifest_size = -1
            try:
                log_size = log_path.stat().st_size
            except OSError:
                log_size = -1
            print(f"Manifest saved: {manifest_path} (bytes={manifest_size})")
            print(f"Log saved: {log_path} (bytes={log_size})")

        def _extract_summary(file_path: Path | None, code: str | None) -> str:
            """Extract summary from script docstring or first comment."""
            content = None
            if file_path and file_path.exists():
                try:
                    content = file_path.read_text(encoding="utf-8")
                except Exception:
                    pass
            elif code:
                content = code
            
            if not content:
                return ""
            
            lines = content.strip().splitlines()
            # Try to extract docstring
            if lines and (lines[0].startswith('"""') or lines[0].startswith("'''")):
                quote = lines[0][:3]
                if quote in lines[0][3:]:
                    # Single line docstring
                    return lines[0][3:].split(quote)[0].strip()[:100]
                # Multi-line docstring
                for i, line in enumerate(lines[1:], 1):
                    if quote in line:
                        return " ".join(lines[0][3:i]).strip()[:100]
            # Try first comment
            if lines and lines[0].startswith("#"):
                return lines[0][1:].strip()[:100]
            return ""

        def _append_history(
            output_dir: Path,
            *,
            run_id: str,
            task: str,
            manifest_path: Path,
            success: bool,
            source_file: Path | None = None,
            code: str | None = None,
        ) -> None:
            """Append task execution to .history.jsonl for learn-skill recall."""
            history_path = output_dir / ".history.jsonl"
            summary = _extract_summary(source_file, code)
            
            entry = {
                "ts": datetime.now().isoformat(timespec="seconds"),
                "run_id": run_id,
                "task": task,
                "manifest": str(manifest_path.name),
                "success": success,
                "summary": summary,
            }
            if source_file:
                entry["source"] = str(source_file.name)
            
            try:
                with history_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            except Exception:
                pass  # Silent fail - history is optional

        # Handle --cwd option
        if args.cwd:
            if not os.path.isdir(args.cwd):
                print(f"Error: Directory does not exist: {args.cwd}", file=sys.stderr)
                sys.exit(1)
            os.chdir(args.cwd)
            # Reload local .env from the new cwd (overrides user config)
            load_dotenv(override=True)

        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = _resolve_base_name()
        output_dir = _resolve_output_dir().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        manifest_path = _resolve_manifest_path(output_dir, base=base, run_id=run_id).resolve()
        log_path = _resolve_log_path(output_dir, base=base, run_id=run_id).resolve()

        os.environ["PYX_RUN_ID"] = run_id
        os.environ["PYX_OUTPUT_DIR"] = str(output_dir)
        # Strategy A: PYX_OUTPUT_PATH is the manifest path.
        os.environ["PYX_OUTPUT_PATH"] = str(manifest_path)
        os.environ["PYX_LOG_PATH"] = str(log_path)
        if getattr(args, "input_path", None):
            os.environ["PYX_INPUT_PATH"] = str(Path(args.input_path).resolve())
        
        timeout = args.timeout if hasattr(args, 'timeout') else None
        is_async = args.is_async if hasattr(args, 'is_async') else False
        
        if args.code:
            if is_async:
                result = run_async_code(args.code, timeout=timeout, output_path=str(log_path))
            else:
                result = run_code(args.code, capture_output=False, timeout=timeout, output_path=str(log_path))

            _ensure_minimal_manifest(manifest_path, run_id=run_id, base=base, log_path=log_path, success=result.success)
            _print_manifest_and_log_summary(manifest_path, log_path)
            _append_history(output_dir, run_id=run_id, task=base, manifest_path=manifest_path, success=result.success, code=args.code)
            if result.error and not result.success:
                print(result.error, file=sys.stderr)
            sys.exit(0 if result.success else 1)
        elif args.file:
            script_args = args.script_args if hasattr(args, 'script_args') else []
            result = run_file(args.file, script_args=script_args, capture_output=False, timeout=timeout, output_path=str(log_path))

            _ensure_minimal_manifest(manifest_path, run_id=run_id, base=base, log_path=log_path, success=result.success)
            _print_manifest_and_log_summary(manifest_path, log_path)
            _append_history(output_dir, run_id=run_id, task=base, manifest_path=manifest_path, success=result.success, source_file=Path(args.file))
            if result.error and not result.success:
                print(result.error, file=sys.stderr)
            sys.exit(0 if result.success else 1)
        elif args.base64:
            if args.yes:
                print("Error: -y/--yes is not allowed with --base64 (confirmation is required).", file=sys.stderr)
                sys.exit(2)
            try:
                code = base64.b64decode(args.base64).decode("utf-8")
            except Exception as e:
                print(f"Error decoding base64: {e}", file=sys.stderr)
                sys.exit(1)
            
            # Always show decoded code
            console.print("\n[bold yellow]Decoded code:[/bold yellow]")
            console.print(Syntax(code, "python", theme="monokai", line_numbers=True))
            console.print()
            
            # Always require confirmation for base64 code
            if not Confirm.ask("Execute this code?", default=True):
                console.print("[dim]Cancelled.[/dim]")
                sys.exit(0)
            
            if is_async:
                result = run_async_code(code, timeout=timeout, output_path=str(log_path))
            else:
                result = run_code(code, capture_output=False, timeout=timeout, output_path=str(log_path))

            _ensure_minimal_manifest(manifest_path, run_id=run_id, base=base, log_path=log_path, success=result.success)
            _print_manifest_and_log_summary(manifest_path, log_path)
            _append_history(output_dir, run_id=run_id, task=base, manifest_path=manifest_path, success=result.success, code=code)
            if result.error and not result.success:
                print(result.error, file=sys.stderr)
            sys.exit(0 if result.success else 1)
    elif args.command == "python":
        # `.env` is loaded at module import time (see top of this file).
        # Apply UV proxy/index settings to environment before exec
        env = get_uv_env()
        os.environ.update(env)
        # Replace the current process with the interpreter so interactive REPL behaves normally.
        python_args = getattr(args, "python_args", None) or []
        if python_args and python_args[0] == "--":
            python_args = python_args[1:]
        os.execv(sys.executable, [sys.executable, *python_args])
    elif args.command == "add":
        result = add_package(args.package)
        if result.output:
            print(result.output)
        if result.error:
            print(result.error, file=sys.stderr)
        sys.exit(0 if result.success else 1)
    elif args.command == "ensure-temp":
        result = ensure_temp(args.dir)
        if result.output:
            print(result.output)
        if result.error:
            print(result.error, file=sys.stderr)
        sys.exit(0 if result.success else 1)
    elif args.command == "info":
        # Determine what to include
        # If no specific flags, show all
        show_all = not any([args.system, args.syntax, args.env, args.commands])
        include_system = show_all or args.system
        include_syntax = show_all or args.syntax
        include_env = show_all or args.env
        include_commands = show_all or args.commands
        
        # Show progress bars for interactive (non-JSON) mode
        show_progress = not args.as_json
        
        info = get_environment_info(
            include_system=include_system,
            include_syntax=include_syntax,
            include_env=include_env,
            include_commands=include_commands,
            show_progress=show_progress,
        )
        
        if args.as_json:
            from dataclasses import asdict
            print(json.dumps(asdict(info), indent=2))
        else:
            output = format_environment_info(
                info,
                include_system=include_system,
                include_syntax=include_syntax,
                include_env=include_env,
                include_commands=include_commands,
            )
            print(output)
        sys.exit(0)
    elif args.command in ("generate-instructions", "gi"):
        output_path = Path(args.output)
        
        markdown: str
        instruction_type: str
        raw_info = None
        env_var_count: int | None = None

        # Generate combined instructions
        console.print("[bold blue]Collecting environment information...[/bold blue]")
        style = getattr(args, "style", "file")
        try:
            markdown, summary = _build_combined_instructions_markdown(parser, style=style)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)

        instruction_type = "instructions"
        raw_info = None
        env_var_count = summary.get("env_variables_count") if isinstance(summary, dict) else None
        
        # Print only mode
        if args.print_only:
            reconfigure = getattr(sys.stdout, "reconfigure", None)
            if callable(reconfigure):
                reconfigure(encoding="utf-8")
            print(_redact_markdown(markdown))
            sys.exit(0)
        
        # Handle existing file - only ask if --ask flag is set (default: auto-backup)
        if output_path.exists() and args.ask and not args.force:
            console.print(f"\n[yellow]File already exists: {output_path}[/yellow]")
            choice = console.input("[bold]Choose action ([r]eplace with backup / [o]verwrite / [c]ancel): [/bold]").lower().strip()
            
            if choice in ("c", "cancel", ""):
                console.print("[dim]Cancelled.[/dim]")
                sys.exit(0)
            elif choice in ("o", "overwrite"):
                args.force = True
            # 'r' or 'replace' will use default backup behavior
        
        # Save the file
        success, saved_path, backup_path = save_with_backup(
            _redact_markdown(markdown),
            output_path,
            force=args.force,
        )
        
        if success:
            console.print(f"\n[green]✓ Generated {instruction_type}:[/green] {saved_path}")
            if backup_path:
                console.print(f"[dim]  Backup created: {backup_path}[/dim]")

            console.print("\n[bold]Summary:[/bold]")
            os_name = summary.get("os") if isinstance(summary, dict) else None
            shell = summary.get("shell") if isinstance(summary, dict) else None
            patterns = summary.get("syntax_patterns_count") if isinstance(summary, dict) else None
            cmds = summary.get("available_commands_count") if isinstance(summary, dict) else None
            total_cmds = summary.get("total_commands_checked") if isinstance(summary, dict) else None
            if os_name and shell:
                console.print(f"  • OS: {os_name} ({shell})")
            if patterns is not None:
                console.print(f"  • Shell syntax patterns: {patterns}")
            if env_var_count is not None:
                console.print(f"  • Environment variables: {env_var_count}")
            if cmds is not None and total_cmds is not None:
                console.print(f"  • Available commands: {cmds}/{total_cmds}")
        else:
            console.print("[red]Error saving file[/red]")
            sys.exit(1)
        
        sys.exit(0)
    elif args.command in ("generate-skill", "gs"):
        output_dir = Path(args.output_dir)
        selected_skill = getattr(args, "skill", "pyx")
        privacy = getattr(args, "privacy", "public")

        def _resolve_all_base_dir(path: Path) -> Path:
            leaf = path.name.strip().lower()
            return path.parent if leaf in ("pyx", "inspect", "summary") else path
        
        # Print only mode - just generate SKILL.md content
        if args.print_only:
            console.print("[bold blue]Collecting environment information...[/bold blue]", file=sys.stderr)
            info = get_environment_info(show_progress=True)

            if selected_skill == "all":
                pyx_md = _generate_skill_md(info)
                inspect_md = _generate_inspect_skill_md(info)
                skill_md = "\n\n---\n\n".join([pyx_md, inspect_md])
            elif selected_skill == "inspect":
                skill_md = _generate_inspect_skill_md(info)
            else:
                skill_md = _generate_skill_md(info)
            
            reconfigure = getattr(sys.stdout, "reconfigure", None)
            if callable(reconfigure):
                reconfigure(encoding="utf-8")
            print(skill_md)
            sys.exit(0)
        
        # Generate skill files
        console.print("[bold blue]Generating Claude skill files...[/bold blue]")
        try:
            if selected_skill == "all":
                base_dir = _resolve_all_base_dir(output_dir)
                results = [
                    generate_skill_files(
                        output_dir=base_dir / "pyx",
                        show_progress=True,
                        force=args.force,
                        skill="pyx",
                        privacy=privacy,
                    ),
                    generate_skill_files(
                        output_dir=base_dir / "inspect",
                        show_progress=True,
                        force=args.force,
                        skill="inspect",
                        privacy=privacy,
                    ),
                    generate_skill_files(
                        output_dir=base_dir / "summary",
                        show_progress=True,
                        force=args.force,
                        skill="summary",
                        privacy=privacy,
                    ),
                ]
                result = results[0]
            else:
                results = []
                result = generate_skill_files(
                    output_dir=output_dir,
                    show_progress=True,
                    force=args.force,
                    skill=selected_skill,
                    privacy=privacy,
                )
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)

        def _print_result(r) -> None:
            if not r.success:
                console.print(f"[red]Error: {r.error}[/red]")
                sys.exit(1)

            console.print(f"\n[green]✓ Generated skill at:[/green] {r.skill_dir}")
            if r.backup_dir:
                console.print(f"[dim]  Backup created: {r.backup_dir}[/dim]")
            console.print("\n[bold]Files created:[/bold]")
            for f in r.files_created:
                try:
                    rel_path = Path(f).relative_to(Path(r.skill_dir)) if r.skill_dir else f
                    console.print(f"  • {rel_path}")
                except ValueError:
                    console.print(f"  • {f}")

        if selected_skill == "all":
            for r in results:
                _print_result(r)
            console.print("\n[dim]To use these skills, copy each directory to your Claude skills folder:[/dim]")
            console.print("[dim]  ~/.claude/skills/<skill>/  (or $CLAUDE_SKILLS_PATH)[/dim]")
        else:
            _print_result(result)
            console.print("\n[dim]To use this skill, copy the directory to your Claude skills folder:[/dim]")
            console.print("[dim]  ~/.claude/skills/<skill>/  (or $CLAUDE_SKILLS_PATH)[/dim]")
        
        sys.exit(0)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
