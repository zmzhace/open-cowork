# -*- coding: utf-8 -*-
"""clipboard tool — read/write system clipboard."""
import pyperclip


TOOL_SCHEMA = {
    "name": "clipboard",
    "description": "Read or write the system clipboard.",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["read", "write"],
                "description": "Read from or write to clipboard",
            },
            "text": {"type": "string", "description": "Text to write (for write action)"},
        },
        "required": ["action"],
    },
}


def execute(action: str, text: str = None, **kwargs) -> dict:
    if action == "read":
        try:
            content = pyperclip.paste()
            return {"content": content[:5000]}
        except Exception as e:
            return {"error": str(e)}

    elif action == "write":
        try:
            pyperclip.copy(text or "")
            return {"result": f"Copied {len(text or '')} chars to clipboard"}
        except Exception as e:
            return {"error": str(e)}

    return {"error": f"Unknown action: {action}"}
