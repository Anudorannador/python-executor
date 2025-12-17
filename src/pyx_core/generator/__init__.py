"""
Generator package for python-executor.

Provides functions to generate LLM-friendly documentation and Claude skills
based on the current environment configuration.
"""

from .common import (
    GenerateInstructionsResult,
    GeneratePyxInstructionsResult,
    GenerateShellInstructionsResult,
    GenerateSkillResult,
    save_with_backup,
)

from .instruction import (
    generate_instructions,
    generate_pyx_instructions,
    generate_shell_instructions,
)

from .skill import (
    generate_skill_files,
    # Expose for CLI --print mode
    _generate_skill_md,
)

__all__ = [
    # Result types
    "GenerateInstructionsResult",
    "GeneratePyxInstructionsResult",
    "GenerateShellInstructionsResult",
    "GenerateSkillResult",
    # Common utilities
    "save_with_backup",
    # Instruction generation
    "generate_instructions",
    "generate_pyx_instructions",
    "generate_shell_instructions",
    # Skill generation
    "generate_skill_files",
    "_generate_skill_md",
]
