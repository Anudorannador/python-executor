"""
MCP Server for python-executor.
Provides tools for LLMs to execute Python code safely.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from pyx_core import run_code, run_file, run_async_code, add_package, ensure_temp, get_environment_info, format_environment_info

logger = logging.getLogger("pyx-mcp")

# Create MCP Server
app = Server("pyx-mcp")


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
            description="Get comprehensive environment information including OS, shell type, shell syntax reference, available commands, and environment variable keys. Use this to understand the execution environment before running commands or code.",
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
                        "description": "Include shell syntax reference (variable expansion, chaining, pipes, etc.). Default: true.",
                        "default": True
                    },
                    "include_env": {
                        "type": "boolean",
                        "description": "Include environment variable keys from .env files. Default: true.",
                        "default": True
                    },
                    "include_commands": {
                        "type": "boolean",
                        "description": "Check availability of common commands (git, curl, docker, etc.). Default: true.",
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
    
    def _format_result(result: Any, action: str = "Execution") -> list[TextContent]:
        """Format ExecutionResult to TextContent."""
        output_parts = []
        if result.output:
            output_parts.append(f"Output:\n{result.output}")
        if result.error:
            output_parts.append(f"Error:\n{result.error}")
        if result.traceback and not result.success:
            output_parts.append(f"Traceback:\n{result.traceback}")
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
        result = run_code(code, cwd=cwd, timeout=timeout)
        return _format_result(result)
    
    elif name == "run_async_python_code":
        code = arguments.get("code", "")
        cwd = arguments.get("cwd")
        timeout = arguments.get("timeout")
        result = run_async_code(code, cwd=cwd, timeout=timeout)
        return _format_result(result, "Async execution")
    
    elif name == "run_python_file":
        file_path = arguments.get("file_path", "")
        cwd = arguments.get("cwd")
        script_args = arguments.get("script_args", [])
        timeout = arguments.get("timeout")
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
