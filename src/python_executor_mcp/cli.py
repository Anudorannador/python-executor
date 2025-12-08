"""
CLI interface for python-executor.
Provides command line access to the executor functions.
"""

import argparse
import sys

from .executor import run_code, run_file, add_package, ensure_temp


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="python-executor",
        description="A cross-platform Python code executor that avoids shell-specific issues.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # run command
    run_parser = subparsers.add_parser("run", help="Run Python code or a script file")
    run_group = run_parser.add_mutually_exclusive_group(required=True)
    run_group.add_argument("--code", "-c", type=str, help="Inline Python code to execute")
    run_group.add_argument("--file", "-f", type=str, help="Path to a Python script file")

    # add command
    add_parser = subparsers.add_parser("add", help="Install a Python package")
    add_parser.add_argument("--package", "-p", type=str, required=True, help="Package name to install")

    # ensure-temp command
    ensure_parser = subparsers.add_parser("ensure-temp", help="Ensure ./temp/ directory exists")
    ensure_parser.add_argument("--dir", "-d", type=str, default="temp", help="Directory to create (default: temp)")

    args = parser.parse_args()

    if args.command == "run":
        if args.code:
            result = run_code(args.code, capture_output=False)
            if result.output:
                print(result.output, end="")
            if result.error:
                print(result.error, file=sys.stderr)
            sys.exit(0 if result.success else 1)
        elif args.file:
            result = run_file(args.file, capture_output=False)
            if result.output:
                print(result.output, end="")
            if result.error:
                print(result.error, file=sys.stderr)
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
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
