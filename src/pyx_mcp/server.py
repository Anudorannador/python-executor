"""
MCP Server for python-executor.
Provides tools for LLMs to execute Python code safely.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Load .env files before importing pyx_core
# Priority (later overrides earlier):
# 1. User config: %APPDATA%\pyx\.env (Windows) or ~/.config/pyx/.env (Unix)
# 2. Local .env from cwd
if sys.platform == "win32":
    _USER_CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home())) / "pyx"
else:
    _USER_CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "pyx"
_USER_ENV_PATH = _USER_CONFIG_DIR / ".env"

if _USER_ENV_PATH.exists():
    load_dotenv(_USER_ENV_PATH, override=False)
load_dotenv(override=True)

from pyx_core import (
    run_code,
    run_file,
    run_async_code,
    add_package,
    ensure_temp,
    get_environment_info,
    format_environment_info,
    generate_instructions,
    generate_pyx_instructions,
    generate_shell_instructions,
    save_with_backup,
)

app = Server("python-executor")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="run_python_code",
            description="Execute inline Python code. Use this for quick calculations, data processing, or any Python operations. The code runs in a fresh namespace with __name__ set to '__main__'. Output is captured and returned.",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute. Can be multi-line. All standard library modules are available, plus pre-installed packages like requests, pandas, numpy, etc."
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory to run the code in. If not specified, uses current directory."
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Maximum execution time in seconds. If not specified, no timeout is applied."
                    },
                    "input_path": {
                        "type": "string",
                        "description": "Optional path to a JSON input file. The server will expose it via env var PYX_INPUT_PATH for your code to read."
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Optional output directory for generated files. Defaults to the directory of input_path if provided, else cwd."
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional manifest path (Strategy A). When provided (or when output_dir is provided), the server will stream stdout/stderr to a log file and ensure a JSON manifest exists at this path, instead of returning large output."
                    }
                },
                "required": ["code"]
            }
        ),
        Tool(
            name="run_async_python_code",
            description="Execute async Python code containing async/await. Use this when your code needs to use asyncio, aiohttp, or other async libraries. Supports top-level await.",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Async Python code to execute. Can contain top-level await statements."
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory to run the code in. If not specified, uses current directory."
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Maximum execution time in seconds. If not specified, no timeout is applied."
                    },
                    "input_path": {
                        "type": "string",
                        "description": "Optional path to a JSON input file. The server will expose it via env var PYX_INPUT_PATH for your code to read."
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Optional output directory for generated files. Defaults to the directory of input_path if provided, else cwd."
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional manifest path (Strategy A). When provided (or when output_dir is provided), the server will stream stdout/stderr to a log file and ensure a JSON manifest exists at this path, instead of returning large output."
                    }
                },
                "required": ["code"]
            }
        ),
        Tool(
            name="run_python_file",
            description="Execute a Python script file. The script runs with __file__ set to its path. Use cwd to specify working directory, and script_args to pass command line arguments.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute or relative path to the Python script file to execute."
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory to run the script in. If not specified, uses the script's directory."
                    },
                    "script_args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Command line arguments to pass to the script (will be set as sys.argv[1:])."
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Maximum execution time in seconds. If not specified, no timeout is applied."
                    },
                    "input_path": {
                        "type": "string",
                        "description": "Optional path to a JSON input file. The server will expose it via env var PYX_INPUT_PATH for your script to read."
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Optional output directory for generated files. Defaults to the directory of input_path if provided, else cwd."
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional manifest path (Strategy A). When provided (or when output_dir is provided), the server will stream stdout/stderr to a log file and ensure a JSON manifest exists at this path, instead of returning large output."
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="install_package",
            description="Install a Python package using uv. Use this when a required package is missing. The package will be added to the project's dependencies.",
            inputSchema={
                "type": "object",
                "properties": {
                    "package": {
                        "type": "string",
                        "description": "Package name to install, e.g. 'requests', 'pandas>=2.0', 'numpy==1.24.0'"
                    }
                },
                "required": ["package"]
            }
        ),
        Tool(
            name="ensure_directory",
            description="Ensure a directory exists in the current workspace. Creates the directory and all parent directories if they don't exist.",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Directory path to create. Default is 'temp'.",
                        "default": "temp"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_environment_info",
            description="Get comprehensive environment information including OS, shell type, dynamically-tested shell syntax support, available commands (111 tools), and environment variable keys. Use this to understand the execution environment before running commands or code.",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_system": {
                        "type": "boolean",
                        "description": "Include OS, shell, Python version info. Default: true.",
                        "default": True
                    },
                    "include_syntax": {
                        "type": "boolean",
                        "description": "Include dynamically-tested shell syntax support (20 patterns: variable, chaining, pipe, redirect, glob, etc.) with pyx alternatives. Default: true.",
                        "default": True
                    },
                    "include_env": {
                        "type": "boolean",
                        "description": "Include environment variable keys from .env files. Default: true.",
                        "default": True
                    },
                    "include_commands": {
                        "type": "boolean",
                        "description": "Check availability of common commands (111 tools: git, curl, docker, etc.). Default: true.",
                        "default": True
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="generate_pyx_instructions",
            description="(Deprecated) Use CLI instead: `pyx gi` for instructions, `pyx gs` for Claude skills. This tool generates pyx-usage markdown but is superseded by the CLI commands.",
            inputSchema={
                "type": "object",
                "properties": {
                    "style": {
                        "type": "string",
                        "description": "Instruction style: 'file' (recommended, file-first) or 'base64' (legacy). Default: 'file'.",
                        "enum": ["file", "base64"],
                        "default": "file"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "File path to save the generated markdown (legacy).",
                        "default": "./docs/pyx.pyx.instructions.md"
                    },
                    "save_to_file": {
                        "type": "boolean",
                        "description": "Whether to save the markdown to file. Default: false (just return content).",
                        "default": False
                    },
                    "backup_existing": {
                        "type": "boolean",
                        "description": "Create numbered backup if file exists. Default: true.",
                        "default": True
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="generate_shell_instructions",
            description="(Deprecated) Use CLI instead: `pyx gi` for instructions, `pyx gs` for Claude skills. This tool generates shell-usage markdown but is superseded by the CLI commands.",
            inputSchema={
                "type": "object",
                "properties": {
                    "output_path": {
                        "type": "string",
                        "description": "File path to save the generated markdown (legacy).",
                        "default": "./docs/pyx.shell.instructions.md"
                    },
                    "save_to_file": {
                        "type": "boolean",
                        "description": "Whether to save the markdown to file. Default: false (just return content).",
                        "default": False
                    },
                    "backup_existing": {
                        "type": "boolean",
                        "description": "Create numbered backup if file exists. Default: true.",
                        "default": True
                    }
                },
                "required": []
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls"""

    MAX_RETURN_CHARS = 8_000

    def _ensure_parent(path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

    def _resolve_output_dir(*, cwd: str | None, input_path: str | None, output_dir: str | None) -> Path:
        if output_dir:
            return Path(output_dir)
        if input_path:
            return Path(input_path).resolve().parent
        if cwd:
            return Path(cwd).resolve()
        return Path.cwd()

    def _resolve_manifest_path(output_dir: Path, *, output_path: str | None, base: str, run_id: str) -> Path:
        if output_path:
            return Path(output_path)
        return output_dir / f"{base}.{run_id}.manifest.json"

    def _resolve_log_path(output_dir: Path, *, base: str, run_id: str) -> Path:
        return output_dir / f"{base}.{run_id}.log.txt"

    def _ensure_minimal_manifest(
        manifest_path: Path,
        *,
        run_id: str,
        success: bool,
        output_dir: Path,
        input_path: str | None,
        log_path: Path,
    ) -> None:
        if manifest_path.exists():
            return
        _ensure_parent(manifest_path)
        payload: dict[str, object] = {
            "run_id": run_id,
            "success": success,
            "output_dir": str(output_dir.resolve()),
            "input_path": str(Path(input_path).resolve()) if input_path else None,
            "outputs": [
                {
                    "path": str(log_path.resolve()),
                    "role": "log",
                    "category": "stdout_stderr",
                    "format": "text",
                }
            ],
        }
        manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _summarize_existing_file(path: Path, label: str = "File") -> str:
        if not path.exists():
            return f"{label} not found: {path}"
        try:
            size = path.stat().st_size
        except OSError:
            size = -1
        return f"{label} saved: {path} (bytes={size})"

    def _truncate(text: str) -> str:
        if len(text) <= MAX_RETURN_CHARS:
            return text
        return text[:MAX_RETURN_CHARS] + "\n\n[TRUNCATED]"

    class _EnvOverride:
        def __init__(self, updates: dict[str, str]) -> None:
            self._updates = updates
            self._previous: dict[str, str | None] = {}

        def __enter__(self) -> None:
            for k, v in self._updates.items():
                self._previous[k] = os.environ.get(k)
                os.environ[k] = v

        def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
            for k, prev in self._previous.items():
                if prev is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = prev
    
    def _format_result(result: Any, action: str = "Execution") -> list[TextContent]:
        """Format ExecutionResult to TextContent."""
        output_parts = []
        if result.output:
            output_parts.append(f"Output:\n{_truncate(result.output)}")
        if result.error:
            output_parts.append(f"Error:\n{_truncate(result.error)}")
        if result.traceback and not result.success:
            output_parts.append(f"Traceback:\n{_truncate(result.traceback)}")
        if not output_parts:
            output_parts.append(f"{action} completed successfully (no output)")
        
        status = "✓" if result.success else "✗"
        return [TextContent(
            type="text",
            text=f"{status} {action} {'succeeded' if result.success else 'failed'}\n\n" + "\n\n".join(output_parts)
        )]
    
    if name == "run_python_code":
        code = arguments.get("code", "")
        cwd = arguments.get("cwd")
        timeout = arguments.get("timeout")
        input_path = arguments.get("input_path")
        output_dir_arg = arguments.get("output_dir")
        output_path = arguments.get("output_path")

        file_mode = bool(output_path or output_dir_arg)
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = "inline"

        if file_mode:
            output_dir = _resolve_output_dir(cwd=cwd, input_path=input_path, output_dir=output_dir_arg).resolve()
            output_dir.mkdir(parents=True, exist_ok=True)
            manifest_path = _resolve_manifest_path(output_dir, output_path=output_path, base=base, run_id=run_id).resolve()
            log_path = _resolve_log_path(output_dir, base=base, run_id=run_id).resolve()

            env_updates: dict[str, str] = {
                "PYX_RUN_ID": run_id,
                "PYX_OUTPUT_DIR": str(output_dir),
                "PYX_OUTPUT_PATH": str(manifest_path),
                "PYX_LOG_PATH": str(log_path),
            }
            if input_path:
                env_updates["PYX_INPUT_PATH"] = str(input_path)

            with _EnvOverride(env_updates):
                result = run_code(code, cwd=cwd, timeout=timeout, output_path=str(log_path))

            _ensure_minimal_manifest(
                manifest_path,
                run_id=run_id,
                success=result.success,
                output_dir=output_dir,
                input_path=input_path,
                log_path=log_path,
            )

            status = "✓" if result.success else "✗"
            summary = "\n".join([
                _summarize_existing_file(manifest_path, label="Manifest"),
                _summarize_existing_file(log_path, label="Log"),
            ])
            return [TextContent(type="text", text=f"{status} Execution {'succeeded' if result.success else 'failed'}\n\n{summary}")]

        env_updates: dict[str, str] = {}
        if input_path:
            env_updates["PYX_INPUT_PATH"] = str(input_path)

        with _EnvOverride(env_updates):
            result = run_code(code, cwd=cwd, timeout=timeout)

        return _format_result(result)
    
    elif name == "run_async_python_code":
        code = arguments.get("code", "")
        cwd = arguments.get("cwd")
        timeout = arguments.get("timeout")
        input_path = arguments.get("input_path")
        output_dir_arg = arguments.get("output_dir")
        output_path = arguments.get("output_path")

        file_mode = bool(output_path or output_dir_arg)
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = "inline"

        if file_mode:
            output_dir = _resolve_output_dir(cwd=cwd, input_path=input_path, output_dir=output_dir_arg).resolve()
            output_dir.mkdir(parents=True, exist_ok=True)
            manifest_path = _resolve_manifest_path(output_dir, output_path=output_path, base=base, run_id=run_id).resolve()
            log_path = _resolve_log_path(output_dir, base=base, run_id=run_id).resolve()

            env_updates: dict[str, str] = {
                "PYX_RUN_ID": run_id,
                "PYX_OUTPUT_DIR": str(output_dir),
                "PYX_OUTPUT_PATH": str(manifest_path),
                "PYX_LOG_PATH": str(log_path),
            }
            if input_path:
                env_updates["PYX_INPUT_PATH"] = str(input_path)

            with _EnvOverride(env_updates):
                result = run_async_code(code, cwd=cwd, timeout=timeout, output_path=str(log_path))

            _ensure_minimal_manifest(
                manifest_path,
                run_id=run_id,
                success=result.success,
                output_dir=output_dir,
                input_path=input_path,
                log_path=log_path,
            )

            status = "✓" if result.success else "✗"
            summary = "\n".join([
                _summarize_existing_file(manifest_path, label="Manifest"),
                _summarize_existing_file(log_path, label="Log"),
            ])
            return [TextContent(type="text", text=f"{status} Async execution {'succeeded' if result.success else 'failed'}\n\n{summary}")]

        env_updates: dict[str, str] = {}
        if input_path:
            env_updates["PYX_INPUT_PATH"] = str(input_path)

        with _EnvOverride(env_updates):
            result = run_async_code(code, cwd=cwd, timeout=timeout)

        return _format_result(result, "Async execution")
    
    elif name == "run_python_file":
        file_path = arguments.get("file_path", "")
        cwd = arguments.get("cwd")
        script_args = arguments.get("script_args", [])
        timeout = arguments.get("timeout")
        input_path = arguments.get("input_path")
        output_dir_arg = arguments.get("output_dir")
        output_path = arguments.get("output_path")

        file_mode = bool(output_path or output_dir_arg)
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = Path(file_path).stem if file_path else "script"

        if file_mode:
            output_dir = _resolve_output_dir(cwd=cwd, input_path=input_path, output_dir=output_dir_arg).resolve()
            output_dir.mkdir(parents=True, exist_ok=True)
            manifest_path = _resolve_manifest_path(output_dir, output_path=output_path, base=base, run_id=run_id).resolve()
            log_path = _resolve_log_path(output_dir, base=base, run_id=run_id).resolve()

            env_updates: dict[str, str] = {
                "PYX_RUN_ID": run_id,
                "PYX_OUTPUT_DIR": str(output_dir),
                "PYX_OUTPUT_PATH": str(manifest_path),
                "PYX_LOG_PATH": str(log_path),
            }
            if input_path:
                env_updates["PYX_INPUT_PATH"] = str(input_path)

            with _EnvOverride(env_updates):
                result = run_file(file_path, script_args=script_args, cwd=cwd, timeout=timeout, output_path=str(log_path))

            _ensure_minimal_manifest(
                manifest_path,
                run_id=run_id,
                success=result.success,
                output_dir=output_dir,
                input_path=input_path,
                log_path=log_path,
            )

            status = "✓" if result.success else "✗"
            summary = "\n".join([
                _summarize_existing_file(manifest_path, label="Manifest"),
                _summarize_existing_file(log_path, label="Log"),
            ])
            return [TextContent(type="text", text=f"{status} Script execution {'succeeded' if result.success else 'failed'}\n\n{summary}")]

        env_updates: dict[str, str] = {}
        if input_path:
            env_updates["PYX_INPUT_PATH"] = str(input_path)

        with _EnvOverride(env_updates):
            result = run_file(file_path, script_args=script_args, cwd=cwd, timeout=timeout)

        return _format_result(result, "Script execution")
    
    elif name == "install_package":
        package = arguments.get("package", "")
        result = add_package(package)
        
        if result.success:
            return [TextContent(
                type="text",
                text=f"✓ Package '{package}' installed successfully\n\n{result.output}"
            )]
        else:
            error_msg = result.error or "Unknown error"
            return [TextContent(
                type="text",
                text=f"✗ Failed to install package '{package}'\n\n{error_msg}"
            )]
    
    elif name == "ensure_directory":
        directory = arguments.get("directory", "temp")
        result = ensure_temp(directory)
        
        if result.success:
            return [TextContent(
                type="text",
                text=f"✓ {result.output}"
            )]
        else:
            error_msg = result.error or "Unknown error"
            return [TextContent(
                type="text",
                text=f"✗ {error_msg}"
            )]
    
    elif name == "get_environment_info":
        include_system = arguments.get("include_system", True)
        include_syntax = arguments.get("include_syntax", True)
        include_env = arguments.get("include_env", True)
        include_commands = arguments.get("include_commands", True)
        
        info = get_environment_info(
            include_system=include_system,
            include_syntax=include_syntax,
            include_env=include_env,
            include_commands=include_commands,
        )
        output = format_environment_info(
            info,
            include_system=include_system,
            include_syntax=include_syntax,
            include_env=include_env,
            include_commands=include_commands,
        )
        
        return [TextContent(
            type="text",
            text=f"✓ Environment Information\n\n{output}"
        )]
    
    elif name == "generate_pyx_instructions":
        import json
        
        style = arguments.get("style", "file")
        output_path = arguments.get("output_path", "./docs/pyx.pyx.instructions.md")
        save_to_file = arguments.get("save_to_file", False)
        backup_existing = arguments.get("backup_existing", True)
        
        # Generate instructions
        result = generate_pyx_instructions(show_progress=False, style=style)
        
        if not result.success:
            return [TextContent(
                type="text",
                text=f"✗ Failed to generate pyx-usage instructions: {result.error}"
            )]
        
        # Optionally save to file
        saved_path = None
        backup_path = None
        if save_to_file and output_path:
            success, saved_path, backup_path = save_with_backup(
                result.markdown,
                output_path,
                force=not backup_existing,
            )
            if not success:
                return [TextContent(
                    type="text",
                    text=f"✗ Failed to save file to {output_path}"
                )]
        
        # Build structured response
        response = {
            "success": True,
            "type": "pyx-usage",
            "markdown": result.markdown,
            "env_keys_with_usage": result.env_keys_with_usage,
            "summary": {
                "os": result.raw_info.os_name,
                "shell": result.raw_info.shell_type,
                "python_version": result.raw_info.python_version,
                "pyx_version": result.raw_info.pyx_version,
                "syntax_patterns_count": len(result.raw_info.syntax_support),
                "env_variables_count": len(result.env_keys_with_usage),
                "available_commands_count": sum(1 for d in result.raw_info.commands.values() if d["available"]),
                "total_commands_checked": len(result.raw_info.commands),
            },
        }
        
        if saved_path:
            response["saved_path"] = saved_path
        if backup_path:
            response["backup_path"] = backup_path
        
        # Return JSON for structured parsing by LLM
        return [TextContent(
            type="text",
            text=json.dumps(response, indent=2)
        )]
    
    elif name == "generate_shell_instructions":
        import json
        
        output_path = arguments.get("output_path", "./docs/pyx.shell.instructions.md")
        save_to_file = arguments.get("save_to_file", False)
        backup_existing = arguments.get("backup_existing", True)
        
        # Generate instructions
        result = generate_shell_instructions(show_progress=False)
        
        if not result.success:
            return [TextContent(
                type="text",
                text=f"✗ Failed to generate shell-usage instructions: {result.error}"
            )]
        
        # Optionally save to file
        saved_path = None
        backup_path = None
        if save_to_file and output_path:
            success, saved_path, backup_path = save_with_backup(
                result.markdown,
                output_path,
                force=not backup_existing,
            )
            if not success:
                return [TextContent(
                    type="text",
                    text=f"✗ Failed to save file to {output_path}"
                )]
        
        # Build structured response
        response = {
            "success": True,
            "type": "shell-usage",
            "markdown": result.markdown,
            "summary": {
                "os": result.raw_info.os_name,
                "shell": result.raw_info.shell_type,
                "python_version": result.raw_info.python_version,
                "syntax_patterns_count": len(result.raw_info.syntax_support),
                "available_commands_count": sum(1 for d in result.raw_info.commands.values() if d["available"]),
                "total_commands_checked": len(result.raw_info.commands),
            },
        }
        
        if saved_path:
            response["saved_path"] = saved_path
        if backup_path:
            response["backup_path"] = backup_path
        
        # Return JSON for structured parsing by LLM
        return [TextContent(
            type="text",
            text=json.dumps(response, indent=2)
        )]
    
    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]


async def run_server():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def main():
    """Entry point for MCP server"""
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
