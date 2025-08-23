"""Environment variable and .env file support for API keys."""

import os
from pathlib import Path
from typing import Dict, Optional

try:
    from dotenv import dotenv_values, load_dotenv
except ImportError:
    # Provide fallback if python-dotenv is not installed
    dotenv_values = None
    load_dotenv = None


def load_api_keys() -> Dict[str, str]:
    """Load API keys from .env files and environment variables.

    Precedence order (highest to lowest):
    1. Environment variables already set
    2. .env file in current directory
    3. .env file in home directory

    Returns:
        Dictionary of environment variables loaded.
    """
    env_vars = {}

    if dotenv_values is None:
        # python-dotenv not installed, just return current environment
        return dict(os.environ)

    # Load from home directory .env first (lowest precedence)
    home_env = Path.home() / ".env"
    if home_env.exists():
        home_vars = dotenv_values(home_env)
        if home_vars:
            env_vars.update(home_vars)

    # Load from current directory .env (higher precedence)
    current_env = Path.cwd() / ".env"
    if current_env.exists():
        current_vars = dotenv_values(current_env)
        if current_vars:
            env_vars.update(current_vars)

    # Load from actual environment (highest precedence)
    # This preserves any already-set environment variables
    for key in ["ZOTERO_API_KEY"]:
        if key in os.environ:
            env_vars[key] = os.environ[key]

    # Set the loaded variables in the environment for use by the app
    for key, value in env_vars.items():
        if value is not None and key not in os.environ:
            os.environ[key] = value

    return env_vars


def get_api_key(cli_value: Optional[str]) -> Optional[str]:
    """Get API key with proper precedence.

    Precedence order (highest to lowest):
    1. Command line argument (if provided)
    2. ZOTERO_API_KEY from environment/.env

    Args:
        cli_value: API key provided via command line.

    Returns:
        The API key to use, or None if not found.
    """
    # Command line takes highest precedence
    if cli_value:
        return cli_value

    # Load from environment/.env files
    env_vars = load_api_keys()
    return env_vars.get("ZOTERO_API_KEY")
