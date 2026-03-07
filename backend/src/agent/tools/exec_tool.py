# -*- coding: utf-8 -*-
"""exec tool — run system commands."""
import subprocess
import os


TOOL_SCHEMA = {
    "name": "exec",
    "description": "Run a system command and return its output. Use this to launch apps, check status, automate tasks. Dangerous commands (format, del /s, shutdown, etc.) are blocked for safety.",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "The command to execute (e.g. 'tasklist', 'start calc', 'dir C:\\\\')"},
            "timeout": {"type": "integer", "description": "Timeout in seconds (default 30)", "default": 30},
            "shell": {"type": "boolean", "description": "Run via shell (default true)", "default": True},
        },
        "required": ["command"],
    },
}

# Dangerous command patterns that should be blocked
DANGEROUS_PATTERNS = [
    "format ", "format.", "rd /s", "del /s", "rmdir /s",
    "rm -rf", "shutdown", "reg delete", "diskpart",
    "bcdedit", "sfc /scannow",
]


def execute(command: str, timeout: int = 30, shell: bool = True, **kwargs) -> dict:
    """Run a system command and return stdout, stderr, exit_code."""
    # Safety check: block dangerous commands
    cmd_lower = command.lower().strip()
    for pattern in DANGEROUS_PATTERNS:
        if pattern in cmd_lower:
            return {
                "stdout": "",
                "stderr": f"⚠️ Dangerous command blocked: '{command}'. Pattern '{pattern}' is not allowed.",
                "exit_code": -1,
            }
    
    try:
        result = subprocess.run(
            command,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.path.expanduser("~"),
            encoding="utf-8",
            errors="replace",
        )
        return {
            "stdout": result.stdout[:5000],  # Cap output
            "stderr": result.stderr[:2000],
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Command timed out", "exit_code": -1}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "exit_code": -1}
