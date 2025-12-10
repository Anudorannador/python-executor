"""
Constants for python-executor.

Contains common commands list and re-exports shell syntax definitions.
"""

from __future__ import annotations

# Re-export shell syntax from shell_syntax module
from .shell_syntax import (
    SYNTAX_PATTERNS,
    SYNTAX_PATTERN_ORDER,
    get_all_syntax_support,
    get_syntax_info,
    test_syntax_support,
    format_syntax_table,
)

# Common commands to check for availability, organized by category
COMMON_COMMANDS: dict[str, list[str]] = {
    # Version Control
    "vcs": ["git", "svn", "hg"],
    
    # Package Managers - Language
    "pkg_lang": [
        "npm", "npx", "yarn", "pnpm",  # JavaScript
        "pip", "uv", "pipx", "conda",   # Python
        "cargo", "rustup",              # Rust
        "go",                           # Go
        "composer",                     # PHP
        "gem", "bundle",                # Ruby
        "maven", "gradle",              # Java
        "nuget",                        # .NET
    ],
    
    # Package Managers - System
    "pkg_system": [
        "brew",                         # macOS
        "apt", "apt-get", "dpkg",       # Debian/Ubuntu
        "yum", "dnf", "rpm",            # RHEL/Fedora
        "pacman",                       # Arch
        "choco", "scoop", "winget",     # Windows
    ],
    
    # Containers & Cloud
    "cloud": [
        "docker", "podman",             # Containers
        "kubectl", "helm",              # Kubernetes
        "terraform",                    # IaC
        "aws", "az", "gcloud",          # Cloud CLIs
    ],
    
    # Programming Languages
    "languages": [
        "python", "python3",
        "node",
        "java", "javac",
        "go",
        "rustc",
        "ruby",
        "php",
        "perl",
        "dotnet",
    ],
    
    # Compilers & Build Tools
    "build": [
        "make", "cmake", "ninja",
        "msbuild",
        "gcc", "g++", "clang", "clang++",
    ],
    
    # Network Tools
    "network": [
        "curl", "wget",
        "ssh", "scp", "rsync",
        "nc", "netcat",
        "ping", "traceroute",
        "nmap",
    ],
    
    # Database Clients
    "database": [
        "mysql", "psql", "sqlite3",
        "mongosh", "mongo",
        "redis-cli",
    ],
    
    # Text Processing
    "text": [
        "grep", "sed", "awk",
        "jq", "yq",
        "rg",  # ripgrep
        "fd",
        "cat", "head", "tail",
        "sort", "uniq", "wc",
    ],
    
    # File & Archive
    "file": [
        "tar", "zip", "unzip",
        "7z", "7za",
        "gzip", "gunzip",
        "xz",
    ],
    
    # Editors
    "editors": [
        "code",  # VS Code
        "vim", "nvim", "nano", "emacs",
    ],
    
    # Utilities
    "utils": [
        "ffmpeg",
        "convert",  # ImageMagick
        "pandoc",
        "gh",  # GitHub CLI
        "htop", "top",
        "tree",
        "watch",
        "xargs",
        "find",
        "which", "whereis",
    ],
}

# Flatten for easy iteration
ALL_COMMANDS: list[str] = []
for _cmds in COMMON_COMMANDS.values():
    ALL_COMMANDS.extend(_cmds)
# Remove duplicates while preserving order
ALL_COMMANDS = list(dict.fromkeys(ALL_COMMANDS))

# Default timeout in seconds (None = no timeout)
DEFAULT_TIMEOUT: float | None = None
