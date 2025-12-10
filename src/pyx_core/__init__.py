# pyx_core - Core execution functions for python-executor
"""
pyx_core - Core execution functions for python-executor.

A cross-platform Python code executor designed for LLM/Agent integration.
"""

__version__ = "0.1.0"

from .constants import (
    COMMON_COMMANDS,
    ALL_COMMANDS,
    DEFAULT_TIMEOUT,
    # Shell syntax exports
    SYNTAX_PATTERNS,
    SYNTAX_PATTERN_ORDER,
    get_all_syntax_support,
    get_syntax_info,
    test_syntax_support,
    format_syntax_table,
)

from .executor import (
    ExecutionResult,
    EnvironmentInfo,
    run_code,
    run_file,
    run_async_code,
    add_package,
    ensure_temp,
    get_environment_info,
    format_environment_info,
)

__all__ = [
    "__version__",
    "ExecutionResult",
    "EnvironmentInfo",
    "run_code",
    "run_file",
    "run_async_code",
    "add_package",
    "ensure_temp",
    "get_environment_info",
    "format_environment_info",
    "DEFAULT_TIMEOUT",
    "COMMON_COMMANDS",
    "ALL_COMMANDS",
    # Shell syntax
    "SYNTAX_PATTERNS",
    "SYNTAX_PATTERN_ORDER",
    "get_all_syntax_support",
    "get_syntax_info",
    "test_syntax_support",
    "format_syntax_table",
]
