"""
MCP Server for python-executor.
Provides tools for LLMs to execute Python code safely.
"""

import asyncio
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .executor import run_code, run_file, add_package, ensure_temp, list_env_keys

logger = logging.getLogger("python-executor-mcp")

# Create MCP Server
app = Server("python-executor-mcp")


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
                    }
                },
                "required": ["code"]
            }
        ),
        Tool(
            name="run_python_file",
            description="Execute a Python script file. The script runs with __file__ set to its path and working directory changed to the script's directory for relative imports.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute or relative path to the Python script file to execute."
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
            name="list_env_keys",
            description="List environment variable keys from .env file in current directory. Only returns key names, not values (to protect secrets). Use this to discover what configuration is available before using os.environ['KEY'] in code.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    
    if name == "run_python_code":
        code = arguments.get("code", "")
        result = run_code(code)
        
        output_parts = []
        if result.output:
            output_parts.append(f"Output:\n{result.output}")
        if result.error:
            output_parts.append(f"Error:\n{result.error}")
        if not output_parts:
            output_parts.append("Code executed successfully (no output)")
        
        status = "✓" if result.success else "✗"
        return [TextContent(
            type="text",
            text=f"{status} Execution {'succeeded' if result.success else 'failed'}\n\n" + "\n\n".join(output_parts)
        )]
    
    elif name == "run_python_file":
        file_path = arguments.get("file_path", "")
        result = run_file(file_path)
        
        output_parts = []
        if result.output:
            output_parts.append(f"Output:\n{result.output}")
        if result.error:
            output_parts.append(f"Error:\n{result.error}")
        if not output_parts:
            output_parts.append("Script executed successfully (no output)")
        
        status = "✓" if result.success else "✗"
        return [TextContent(
            type="text",
            text=f"{status} Execution {'succeeded' if result.success else 'failed'}\n\n" + "\n\n".join(output_parts)
        )]
    
    elif name == "install_package":
        package = arguments.get("package", "")
        result = add_package(package)
        
        if result.success:
            return [TextContent(
                type="text",
                text=f"✓ Package '{package}' installed successfully\n\n{result.output}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"✗ Failed to install package '{package}'\n\n{result.error}"
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
            return [TextContent(
                type="text",
                text=f"✗ {result.error}"
            )]
    
    elif name == "list_env_keys":
        result = list_env_keys()
        
        if result.success:
            return [TextContent(
                type="text",
                text=f"✓ Available environment keys:\n{result.output}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"✗ {result.error}"
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
