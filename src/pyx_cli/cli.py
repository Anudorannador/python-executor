"""
CLI interface for python-executor.
Provides command line access to the executor functions.
"""

from __future__ import annotations

import argparse
import base64
import os
import sys
from pathlib import Path
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
    generate_pyx_instructions,
    generate_shell_instructions,
    save_with_backup,
)

console = Console()


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

    # generate-instructions command (alias: gi) with subcommands
    gen_parser = subparsers.add_parser(
        "generate-instructions",
        aliases=["gi"],
        help="Generate LLM instructions markdown file from environment info",
    )
    gen_subparsers = gen_parser.add_subparsers(dest="gi_subcommand", help="Instruction type to generate")

    # pyx-usage subcommand
    default_pyx_output = os.environ.get("PYX_PYX_INSTRUCTIONS_PATH", "./docs/pyx.pyx.instructions.md")
    default_pyx_style = os.environ.get("PYX_PYX_INSTRUCTIONS_STYLE", "file")
    pyx_usage_parser = gen_subparsers.add_parser("pyx-usage", help="Generate instructions for using pyx instead of shell commands")
    pyx_usage_parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=default_pyx_output,
        help=f"Output path (default: $PYX_PYX_INSTRUCTIONS_PATH or {default_pyx_output})",
    )
    pyx_usage_parser.add_argument(
        "--style",
        type=str,
        choices=["file", "base64"],
        default=default_pyx_style if default_pyx_style in ("file", "base64") else "file",
        help="Instruction style: 'file' (recommended, file-first) or 'base64' (legacy). Default: $PYX_PYX_INSTRUCTIONS_STYLE or 'file'.",
    )
    pyx_usage_parser.add_argument("--ask", action="store_true", help="Ask before replacing existing file (default: auto-backup)")
    pyx_usage_parser.add_argument("--force", action="store_true", help="Overwrite without backup")
    pyx_usage_parser.add_argument("--print", dest="print_only", action="store_true", help="Print markdown to stdout instead of saving")

    # shell-usage subcommand
    default_shell_output = os.environ.get("PYX_SHELL_INSTRUCTIONS_PATH", "./docs/pyx.shell.instructions.md")
    shell_usage_parser = gen_subparsers.add_parser("shell-usage", help="Generate instructions for using the current shell correctly")
    shell_usage_parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=default_shell_output,
        help=f"Output path (default: $PYX_SHELL_INSTRUCTIONS_PATH or {default_shell_output})",
    )
    shell_usage_parser.add_argument("--ask", action="store_true", help="Ask before replacing existing file (default: auto-backup)")
    shell_usage_parser.add_argument("--force", action="store_true", help="Overwrite without backup")
    shell_usage_parser.add_argument("--print", dest="print_only", action="store_true", help="Print markdown to stdout instead of saving")

    # pyx-help subcommand
    default_help_output = os.environ.get("PYX_PYX_HELP_INSTRUCTIONS_PATH", "./docs/pyx.pyx-help.instructions.md")
    pyx_help_parser = gen_subparsers.add_parser("pyx-help", help="Generate a markdown file with `pyx --help` and all subcommand `--help` outputs")
    pyx_help_parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=default_help_output,
        help=f"Output path (default: $PYX_PYX_HELP_INSTRUCTIONS_PATH or {default_help_output})",
    )
    pyx_help_parser.add_argument("--ask", action="store_true", help="Ask before replacing existing file (default: auto-backup)")
    pyx_help_parser.add_argument("--force", action="store_true", help="Overwrite without backup")
    pyx_help_parser.add_argument("--print", dest="print_only", action="store_true", help="Print markdown to stdout instead of saving")

    return parser, gen_parser


def main() -> NoReturn | None:
    """Main CLI entry point"""
    parser, gen_parser = build_parser()

    args = parser.parse_args()

    if args.command == "run":
        # Handle --cwd option
        if args.cwd:
            if not os.path.isdir(args.cwd):
                print(f"Error: Directory does not exist: {args.cwd}", file=sys.stderr)
                sys.exit(1)
            os.chdir(args.cwd)
        
        timeout = args.timeout if hasattr(args, 'timeout') else None
        is_async = args.is_async if hasattr(args, 'is_async') else False
        
        if args.code:
            if is_async:
                result = run_async_code(args.code, timeout=timeout)
            else:
                result = run_code(args.code, capture_output=False, timeout=timeout)
            if result.output:
                print(result.output, end="")
            if result.error:
                print(result.error, file=sys.stderr)
            if result.traceback and not result.success:
                print(result.traceback, file=sys.stderr)
            sys.exit(0 if result.success else 1)
        elif args.file:
            script_args = args.script_args if hasattr(args, 'script_args') else []
            result = run_file(args.file, script_args=script_args, capture_output=False, timeout=timeout)
            if result.output:
                print(result.output, end="")
            if result.error:
                print(result.error, file=sys.stderr)
            if result.traceback and not result.success:
                print(result.traceback, file=sys.stderr)
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
                result = run_async_code(code, timeout=timeout)
            else:
                result = run_code(code, capture_output=False, timeout=timeout)
            if result.output:
                print(result.output, end="")
            if result.error:
                print(result.error, file=sys.stderr)
            if result.traceback and not result.success:
                print(result.traceback, file=sys.stderr)
            sys.exit(0 if result.success else 1)
    elif args.command == "python":
        # `.env` is loaded at module import time (see top of this file).
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
            import json
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
        from pathlib import Path
        
        # Check if subcommand was provided
        if not hasattr(args, 'gi_subcommand') or args.gi_subcommand is None:
            gen_parser.print_help()
            console.print("\n[yellow]Please specify a subcommand: pyx-usage, shell-usage, or pyx-help[/yellow]")
            sys.exit(1)
        
        output_path = Path(args.output)
        
        markdown: str
        instruction_type: str
        raw_info = None
        env_var_count: int | None = None

        if args.gi_subcommand in ("pyx-usage", "shell-usage"):
            # Generate instructions with progress bars
            console.print("[bold blue]Collecting environment information...[/bold blue]")

            if args.gi_subcommand == "pyx-usage":
                style = getattr(args, "style", "file")
                pyx_result = generate_pyx_instructions(show_progress=True, style=style)
                instruction_type = "pyx-usage"
            else:
                shell_result = generate_shell_instructions(show_progress=True)
                instruction_type = "shell-usage"

            if args.gi_subcommand == "pyx-usage":
                if not pyx_result.success:
                    console.print(f"[red]Error: {pyx_result.error}[/red]")
                    sys.exit(1)
                markdown = pyx_result.markdown
                raw_info = pyx_result.raw_info
                env_var_count = len(pyx_result.env_keys_with_usage)
            else:
                if not shell_result.success:
                    console.print(f"[red]Error: {shell_result.error}[/red]")
                    sys.exit(1)
                markdown = shell_result.markdown
                raw_info = shell_result.raw_info
        elif args.gi_subcommand == "pyx-help":
            console.print("[bold blue]Generating pyx help output...[/bold blue]")
            markdown = _generate_pyx_help_instructions_markdown(parser)
            instruction_type = "pyx-help"
        else:
            console.print(f"[red]Unknown subcommand: {args.gi_subcommand}[/red]")
            sys.exit(1)
        
        # Print only mode
        if args.print_only:
            reconfigure = getattr(sys.stdout, "reconfigure", None)
            if callable(reconfigure):
                reconfigure(encoding="utf-8")
            print(markdown)
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
            markdown,
            output_path,
            force=args.force,
        )
        
        if success:
            console.print(f"\n[green]✓ Generated {instruction_type} instructions:[/green] {saved_path}")
            if backup_path:
                console.print(f"[dim]  Backup created: {backup_path}[/dim]")

            if raw_info is not None:
                # Show summary (environment-based instruction types)
                console.print("\n[bold]Summary:[/bold]")
                console.print(f"  • OS: {raw_info.os_name} ({raw_info.shell_type})")
                console.print(f"  • Shell syntax patterns: {len(raw_info.syntax_support)}")
                if env_var_count is not None:
                    console.print(f"  • Environment variables: {env_var_count}")
                available_cmds = sum(1 for d in raw_info.commands.values() if d["available"])
                console.print(f"  • Available commands: {available_cmds}/{len(raw_info.commands)}")
        else:
            console.print("[red]Error saving file[/red]")
            sys.exit(1)
        
        sys.exit(0)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
