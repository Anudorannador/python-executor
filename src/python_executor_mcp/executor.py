"""
Core execution functions for python-executor.
"""

import io
import os
import subprocess
import sys
import traceback
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExecutionResult:
    """Result of code execution."""
    success: bool
    output: str
    error: str | None = None


def run_code(code: str, capture_output: bool = True) -> ExecutionResult:
    """
    Execute inline Python code.
    
    Args:
        code: Python code to execute
        capture_output: If True, capture stdout/stderr; if False, print directly
        
    Returns:
        ExecutionResult with success status and output
    """
    if capture_output:
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, {"__name__": "__main__"})
            return ExecutionResult(
                success=True,
                output=stdout_capture.getvalue(),
                error=stderr_capture.getvalue() or None
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output=stdout_capture.getvalue(),
                error=f"{traceback.format_exc()}"
            )
    else:
        try:
            exec(code, {"__name__": "__main__"})
            return ExecutionResult(success=True, output="")
        except Exception as e:
            return ExecutionResult(success=False, output="", error=str(e))


def run_file(file_path: str, capture_output: bool = True) -> ExecutionResult:
    """
    Execute a Python script file.
    
    Args:
        file_path: Path to the Python script
        capture_output: If True, capture stdout/stderr; if False, print directly
        
    Returns:
        ExecutionResult with success status and output
    """
    path = Path(file_path)
    
    if not path.exists():
        return ExecutionResult(
            success=False,
            output="",
            error=f"File not found: {file_path}"
        )
    
    if not path.is_file():
        return ExecutionResult(
            success=False,
            output="",
            error=f"Not a file: {file_path}"
        )

    # Try multiple encodings
    code = None
    for encoding in ["utf-8", "utf-8-sig", "utf-16", "cp1252", "latin-1"]:
        try:
            code = path.read_text(encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    
    if code is None:
        return ExecutionResult(
            success=False,
            output="",
            error="Unable to decode file with supported encodings"
        )

    # Set up globals with __file__ pointing to the script
    script_globals = {
        "__name__": "__main__",
        "__file__": str(path.resolve()),
    }
    
    # Change to script directory for relative imports
    original_cwd = os.getcwd()
    
    if capture_output:
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        try:
            os.chdir(path.parent.resolve())
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, script_globals)
            return ExecutionResult(
                success=True,
                output=stdout_capture.getvalue(),
                error=stderr_capture.getvalue() or None
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output=stdout_capture.getvalue(),
                error=f"{traceback.format_exc()}"
            )
        finally:
            os.chdir(original_cwd)
    else:
        try:
            os.chdir(path.parent.resolve())
            exec(code, script_globals)
            return ExecutionResult(success=True, output="")
        except Exception as e:
            return ExecutionResult(success=False, output="", error=str(e))
        finally:
            os.chdir(original_cwd)


def add_package(package: str) -> ExecutionResult:
    """
    Install a package using uv.
    
    Args:
        package: Package name to install
        
    Returns:
        ExecutionResult with success status and output
    """
    try:
        result = subprocess.run(
            ["uv", "add", package],
            check=True,
            capture_output=True,
            text=True,
        )
        output = result.stdout
        if result.stderr:
            output += f"\n{result.stderr}"
        return ExecutionResult(success=True, output=output.strip())
    except subprocess.CalledProcessError as e:
        error_msg = f"Error installing package: {e}"
        if e.stdout:
            error_msg += f"\n{e.stdout}"
        if e.stderr:
            error_msg += f"\n{e.stderr}"
        return ExecutionResult(success=False, output="", error=error_msg)
    except FileNotFoundError:
        return ExecutionResult(
            success=False,
            output="",
            error="'uv' command not found. Please install uv first."
        )


def ensure_temp(directory: str = "temp") -> ExecutionResult:
    """
    Ensure a directory exists in the current workspace.
    
    Args:
        directory: Directory name to create (default: "temp")
        
    Returns:
        ExecutionResult with success status and output
    """
    try:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        abs_path = path.resolve()
        return ExecutionResult(
            success=True,
            output=f"Ensured directory exists: {abs_path}"
        )
    except Exception as e:
        return ExecutionResult(
            success=False,
            output="",
            error=f"Error creating directory: {e}"
        )
