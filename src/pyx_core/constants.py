"""
Constants for python-executor.

Contains shell syntax definitions and common commands list.
"""

from __future__ import annotations

# Shell syntax definitions for different shells
SHELL_SYNTAX: dict[str, dict[str, str]] = {
    "powershell": {
        "variable": "$env:VAR or $VAR",
        "chaining_always": "cmd1; cmd2",
        "chaining_on_success": "cmd1 && cmd2",
        "chaining_on_fail": "cmd1 || cmd2",
        "pipe": "|",
        "redirect_stdout": ">",
        "redirect_stderr": "2>",
        "redirect_both": "*>",
        "background": "Start-Process cmd",
        "path_separator": "\\ (also /)",
        "escape_char": "`",
        "string_literal": "'...'",
        "string_interpolated": '"..."',
        "command_substitution": "$(cmd)",
        "null_device": "$null",
        "home_dir": "$HOME",
        "line_continuation": "`",
        "comment": "#",
    },
    "cmd": {
        "variable": "%VAR%",
        "chaining_always": "cmd1 & cmd2",
        "chaining_on_success": "cmd1 && cmd2",
        "chaining_on_fail": "cmd1 || cmd2",
        "pipe": "|",
        "redirect_stdout": ">",
        "redirect_stderr": "2>",
        "redirect_both": "> file 2>&1",
        "background": "start /b cmd",
        "path_separator": "\\",
        "escape_char": "^",
        "string_literal": "N/A",
        "string_interpolated": '"..."',
        "command_substitution": "for /f",
        "null_device": "NUL",
        "home_dir": "%USERPROFILE%",
        "line_continuation": "^",
        "comment": "REM or ::",
    },
    "bash": {
        "variable": "$VAR",
        "chaining_always": "cmd1; cmd2",
        "chaining_on_success": "cmd1 && cmd2",
        "chaining_on_fail": "cmd1 || cmd2",
        "pipe": "|",
        "redirect_stdout": ">",
        "redirect_stderr": "2>",
        "redirect_both": "&> or 2>&1",
        "background": "cmd &",
        "path_separator": "/",
        "escape_char": "\\",
        "string_literal": "'...'",
        "string_interpolated": '"..."',
        "command_substitution": "$(cmd)",
        "null_device": "/dev/null",
        "home_dir": "$HOME or ~",
        "line_continuation": "\\",
        "comment": "#",
    },
    "zsh": {
        "variable": "$VAR",
        "chaining_always": "cmd1; cmd2",
        "chaining_on_success": "cmd1 && cmd2",
        "chaining_on_fail": "cmd1 || cmd2",
        "pipe": "|",
        "redirect_stdout": ">",
        "redirect_stderr": "2>",
        "redirect_both": "&> or 2>&1",
        "background": "cmd &",
        "path_separator": "/",
        "escape_char": "\\",
        "string_literal": "'...'",
        "string_interpolated": '"..."',
        "command_substitution": "$(cmd)",
        "null_device": "/dev/null",
        "home_dir": "$HOME or ~",
        "line_continuation": "\\",
        "comment": "#",
    },
}

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
