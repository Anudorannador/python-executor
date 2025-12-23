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
    build_skill_artifacts,
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


def build_parser() -> argparse.ArgumentParser:
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

    # generate-skill command (alias: gs)
    skill_parser = subparsers.add_parser(
        "generate-skill",
        aliases=["gs"],
        help="Generate the pyx Claude skill (interactive; prints preview then optionally saves)",
    )

    return parser


def main() -> NoReturn | None:
    """Main CLI entry point"""
    parser = build_parser()

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
    elif args.command in ("generate-skill", "gs"):
        def _prompt_privacy() -> str:
            console.print("\n[bold]Privacy mode[/bold]")
            console.print("  1) public (recommended; avoids machine-specific paths)")
            console.print("  2) local  (may include absolute paths; do NOT commit)")
            choice = console.input("Select [1/2] (default: 1): ").strip()
            return "local" if choice == "2" else "public"

        def _prompt_output_dir() -> Path:
            console.print("\n[bold]Output directory[/bold]")
            console.print("  1) docs\\pyx (default)")
            console.print(r"  2) %USERPROFILE%\\.claude\\skills\\pyx")
            console.print("  3) custom path")
            choice = console.input("Select [1/2/3] (default: 1): ").strip() or "1"
            if choice == "2":
                return Path.home() / ".claude" / "skills" / "pyx"
            if choice == "3":
                custom = console.input("Enter output directory path (default: docs\\pyx): ").strip()
                return Path(custom) if custom else (Path("docs") / "pyx")
            return Path("docs") / "pyx"

        privacy = _prompt_privacy()

        console.print("\n[bold blue]Generating pyx skill preview...[/bold blue]")
        try:
            artifacts = build_skill_artifacts(show_progress=True, skill="pyx", privacy=privacy)  # type: ignore[arg-type]
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)

        # Always print generated content first
        for rel_path in sorted(artifacts.keys(), key=lambda p: p.as_posix()):
            console.print(f"\n[bold]=== {rel_path.as_posix()} ===[/bold]")
            console.print(Syntax(artifacts[rel_path], "markdown", theme="monokai", line_numbers=False))

        console.print("")
        if not Confirm.ask("Save these files?", default=True):
            console.print("[dim]Not saved.[/dim]")
            sys.exit(0)

        overwrite = Confirm.ask("If the target exists, overwrite it?", default=False)
        output_dir = _prompt_output_dir().expanduser().resolve()

        if output_dir.exists():
            if not overwrite:
                console.print(f"[yellow]Target already exists:[/yellow] {output_dir}")
                console.print("[dim]Cancelled (not overwriting).[/dim]")
                sys.exit(0)
            if not output_dir.is_dir():
                console.print(f"[red]Target exists but is not a directory:[/red] {output_dir}")
                sys.exit(1)
            shutil.rmtree(output_dir)

        for rel_path, content in artifacts.items():
            out_path = output_dir / rel_path
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(content, encoding="utf-8")

        console.print(f"\n[green]✓ Saved pyx skill to:[/green] {output_dir}")
        sys.exit(0)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
