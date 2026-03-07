# -*- coding: utf-8 -*-
"""file tool — read/write/list files."""
import os


TOOL_SCHEMA = {
    "name": "file",
    "description": "Read, write, or list files and directories.",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["read", "write", "list"],
                "description": "Action to perform",
            },
            "path": {"type": "string", "description": "File or directory path"},
            "content": {"type": "string", "description": "Content to write (for write action)"},
        },
        "required": ["action", "path"],
    },
}


def execute(action: str, path: str, content: str = None, **kwargs) -> dict:
    path = os.path.expanduser(path)

    if action == "read":
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                data = f.read(50000)  # Cap at 50KB
            return {"content": data, "size": os.path.getsize(path)}
        except Exception as e:
            return {"error": str(e)}

    elif action == "write":
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content or "")
            return {"result": f"Written {len(content or '')} chars to {path}"}
        except Exception as e:
            return {"error": str(e)}

    elif action == "list":
        try:
            entries = []
            for name in os.listdir(path)[:100]:
                full = os.path.join(path, name)
                is_dir = os.path.isdir(full)
                size = os.path.getsize(full) if not is_dir else None
                entries.append({"name": name, "is_dir": is_dir, "size": size})
            return {"entries": entries, "path": path}
        except Exception as e:
            return {"error": str(e)}

    return {"error": f"Unknown action: {action}"}
