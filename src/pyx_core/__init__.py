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
    ENV_PATTERNS,
    # Shell syntax exports (re-exported from constants)
    SYNTAX_PATTERNS,
    SYNTAX_PATTERN_ORDER,
    get_all_syntax_support,
    get_syntax_info,
    test_syntax_support,
    format_syntax_table,
)

from .executor import (
    ExecutionResult,
    run_code,
    run_file,
    run_async_code,
    add_package,
    ensure_temp,
)

from .environment import (
    EnvironmentInfo,
    get_environment_info,
    format_environment_info,
    guess_env_usage,
    get_env_with_usage,
)

from .generator import (
    GenerateInstructionsResult,
    GeneratePyxInstructionsResult,
    GenerateShellInstructionsResult,
    generate_instructions,
    generate_pyx_instructions,
    generate_shell_instructions,
    save_with_backup,
)

__all__ = [
    "__version__",
    # Executor
    "ExecutionResult",
    "run_code",
    "run_file",
    "run_async_code",
    "add_package",
    "ensure_temp",
    # Environment
    "EnvironmentInfo",
    "get_environment_info",
    "format_environment_info",
    "guess_env_usage",
    "get_env_with_usage",
    # Generator
    "GenerateInstructionsResult",
    "GeneratePyxInstructionsResult",
    "GenerateShellInstructionsResult",
    "generate_instructions",
    "generate_pyx_instructions",
    "generate_shell_instructions",
    "save_with_backup",
    # Constants
    "DEFAULT_TIMEOUT",
    "COMMON_COMMANDS",
    "ALL_COMMANDS",
    "ENV_PATTERNS",
    # Shell syntax
    "SYNTAX_PATTERNS",
    "SYNTAX_PATTERN_ORDER",
    "get_all_syntax_support",
    "get_syntax_info",
    "test_syntax_support",
    "format_syntax_table",
]
