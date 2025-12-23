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
    build_skill_artifacts,
    generate_skill_files,
    # Expose for CLI --print mode
    _generate_skill_md,
    _generate_inspect_skill_md,
)

from .summary import (
    build_summary_skill_md,
    build_leader_summary_template_md,
    build_markdown_images_md,
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
    "build_skill_artifacts",
    "generate_skill_files",
    "_generate_skill_md",
    "_generate_inspect_skill_md",
    # Summary skill content
    "build_summary_skill_md",
    "build_leader_summary_template_md",
    "build_markdown_images_md",
]
