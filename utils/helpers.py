# utils/helpers.py
# Shared utilities for the Healthcare Mini Agent

import os
from dotenv import load_dotenv

# ── Environment ────────────────────────────────────────────────────────────────

def get_api_key() -> str:
    """Load and return the Anthropic API key from .env."""
    load_dotenv()
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError("ANTHROPIC_API_KEY not found. Check your .env file.")
    return key

# ── Display helpers ────────────────────────────────────────────────────────────

def print_separator(char: str = "─", width: int = 60) -> None:
    """Print a visual separator line."""
    print(char * width)

def print_tool_result(tool_name: str, result: str) -> None:
    """Print a formatted tool result block."""
    print_separator()
    print(f"🔧 Tool: {tool_name}")
    print_separator("·")
    print(result)
    print_separator()