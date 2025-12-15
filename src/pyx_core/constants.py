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
        "pip", "uv", "pipx", "conda", "poetry", "pipenv",  # Python
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
        "python", "python3", "py",
        "node",
        "java", "javac",
        "go",
        "rustc",
        "ruby",
        "php",
        "perl",
        "dotnet",
    ],

    # Python Dev Tools
    "python_tools": [
        "pytest", "tox",
        "ruff", "black", "isort", "mypy",
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
        "pwsh", "powershell",
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

# ==============================================================================
# Environment Variable Usage Patterns
# ==============================================================================

# Patterns for guessing environment variable usage
ENV_PATTERNS: dict[str, tuple[list[str], str]] = {
    # Cloud Providers
    "aws": (["AWS_", "AMAZON_"], "AWS credential or configuration"),
    "azure": (["AZURE_", "AZ_"], "Azure credential or configuration"),
    "gcp": (["GCP_", "GOOGLE_", "GCLOUD_"], "Google Cloud credential or configuration"),
    
    # AI/ML APIs
    "openai": (["OPENAI_"], "OpenAI API configuration"),
    "anthropic": (["ANTHROPIC_", "CLAUDE_"], "Anthropic/Claude API configuration"),
    "huggingface": (["HF_", "HUGGINGFACE_"], "Hugging Face configuration"),
    
    # Database
    "database": (["DB_", "DATABASE_", "MYSQL_", "POSTGRES_", "PG_", "MONGO_", "REDIS_", "SQL_"], "Database connection or configuration"),
    
    # Authentication & Security
    "auth": (["AUTH_", "JWT_", "OAUTH_", "SSO_"], "Authentication configuration"),
    "api_key": (["_API_KEY", "_APIKEY", "API_KEY"], "API key credential"),
    "secret": (["_SECRET", "SECRET_", "_TOKEN", "TOKEN_"], "Secret or token credential"),
    "password": (["_PASSWORD", "_PASS", "_PWD"], "Password credential"),
    
    # Networking & URLs
    "url": (["_URL", "_URI", "_ENDPOINT", "_HOST"], "Service URL or endpoint"),
    "port": (["_PORT"], "Network port configuration"),
    
    # Email
    "email": (["SMTP_", "EMAIL_", "MAIL_", "SENDGRID_", "MAILGUN_"], "Email service configuration"),
    
    # Microsoft/Office
    "microsoft": (["MS_", "MICROSOFT_", "OFFICE_", "GRAPH_", "SHAREPOINT_", "EXCHANGE_"], "Microsoft/Office 365 configuration"),
    
    # Messaging & Notifications
    "slack": (["SLACK_"], "Slack integration configuration"),
    "discord": (["DISCORD_"], "Discord integration configuration"),
    "telegram": (["TELEGRAM_", "TG_"], "Telegram integration configuration"),
    "webhook": (["WEBHOOK_", "_WEBHOOK"], "Webhook configuration"),
    
    # Storage
    "storage": (["S3_", "BLOB_", "STORAGE_", "BUCKET_"], "Cloud storage configuration"),
    
    # Logging & Monitoring
    "logging": (["LOG_", "LOGGING_", "SENTRY_", "DATADOG_", "NEWRELIC_"], "Logging or monitoring configuration"),
    
    # Environment & Deploy
    "env": (["NODE_ENV", "ENVIRONMENT", "ENV", "DEBUG", "PROD", "DEV"], "Environment or deployment configuration"),
    "path": (["PATH", "_PATH", "_DIR", "_DIRECTORY", "_FOLDER"], "File system path configuration"),
}
