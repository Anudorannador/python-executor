"""
CLI interface for python-executor.
Provides command line access to the executor functions.
"""

from __future__ import annotations

import argparse
import base64
import os
import sys
from typing import NoReturn

from rich.console import Console
from rich.prompt import Confirm
from rich.syntax import Syntax

from pyx_core import (
    __version__,
    run_code,
    run_file,
    run_async_code,
    add_package,
    ensure_temp,
    get_environment_info,
    format_environment_info,
)

console = Console()


def main() -> NoReturn | None:
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="pyx",
        description="A cross-platform Python code executor that avoids shell-specific issues.",
    )
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"%(prog)s {__version__}"
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
    run_parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt for base64 code")
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
            try:
                code = base64.b64decode(args.base64).decode("utf-8")
            except Exception as e:
                print(f"Error decoding base64: {e}", file=sys.stderr)
                sys.exit(1)
            
            # Always show decoded code
            console.print("\n[bold yellow]Decoded code:[/bold yellow]")
            console.print(Syntax(code, "python", theme="monokai", line_numbers=True))
            console.print()
            
            # Ask for confirmation unless -y is specified
            if not args.yes:
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
        
        info = get_environment_info(
            include_system=include_system,
            include_syntax=include_syntax,
            include_env=include_env,
            include_commands=include_commands,
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
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
