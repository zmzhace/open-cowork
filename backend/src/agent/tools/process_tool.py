# -*- coding: utf-8 -*-
"""process tool — list/kill running processes."""
import subprocess


TOOL_SCHEMA = {
    "name": "process",
    "description": "List running processes (optionally filter by name) or kill a process by PID.",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list", "kill"],
                "description": "Action: list processes or kill one",
            },
            "filter": {"type": "string", "description": "Filter process name (for list)"},
            "pid": {"type": "integer", "description": "PID to kill (for kill)"},
        },
        "required": ["action"],
    },
}


def execute(action: str, filter: str = None, pid: int = None, **kwargs) -> dict:
    if action == "list":
        cmd = 'tasklist /FO CSV /NH'
        if filter:
            cmd = f'tasklist /FO CSV /NH | findstr /I "{filter}"'
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace")
            processes = []
            for line in result.stdout.strip().split('\n'):
                parts = [p.strip('"') for p in line.split('","')]
                if len(parts) >= 2:
                    processes.append({"name": parts[0], "pid": int(parts[1]) if parts[1].isdigit() else parts[1]})
            return {"processes": processes[:50], "count": len(processes)}
        except Exception as e:
            return {"error": str(e)}

    elif action == "kill":
        if not pid:
            return {"error": "PID required"}
        try:
            result = subprocess.run(f'taskkill /PID {pid} /F', shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
            return {"result": result.stdout.strip(), "exit_code": result.returncode}
        except Exception as e:
            return {"error": str(e)}

    return {"error": f"Unknown action: {action}"}
