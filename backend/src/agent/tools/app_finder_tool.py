# -*- coding: utf-8 -*-
"""app_finder tool — find installed applications on Windows."""
import subprocess
import os
import winreg


TOOL_SCHEMA = {
    "name": "app_finder",
    "description": "Find installed applications on this computer. Searches registry, Start Menu, and common paths.",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "App name to search for (e.g. 'WeChat', 'Chrome', 'WeGame')"},
        },
        "required": ["name"],
    },
}


def _search_registry(name: str) -> list:
    """Search Windows registry for installed apps."""
    results = []
    reg_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    for hive, path in reg_paths:
        try:
            key = winreg.OpenKey(hive, path)
            for i in range(winreg.QueryInfoKey(key)[0]):
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    subkey = winreg.OpenKey(key, subkey_name)
                    try:
                        display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                        if name.lower() in display_name.lower() or name.lower() in subkey_name.lower():
                            entry = {"name": display_name}
                            try:
                                entry["install_location"] = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                            except FileNotFoundError:
                                pass
                            try:
                                icon = winreg.QueryValueEx(subkey, "DisplayIcon")[0]
                                if icon and os.path.exists(icon.strip('"').split(',')[0]):
                                    entry["exe_path"] = icon.strip('"').split(',')[0]
                            except FileNotFoundError:
                                pass
                            results.append(entry)
                    except FileNotFoundError:
                        pass
                    finally:
                        winreg.CloseKey(subkey)
                except (OSError, WindowsError):
                    pass
            winreg.CloseKey(key)
        except (OSError, WindowsError):
            pass
    return results


def _search_start_menu(name: str) -> list:
    """Search Start Menu shortcuts."""
    results = []
    start_dirs = [
        os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
        r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
    ]
    name_lower = name.lower()
    for start_dir in start_dirs:
        if not os.path.exists(start_dir):
            continue
        for root, dirs, files in os.walk(start_dir):
            for f in files:
                if name_lower in f.lower() and f.endswith('.lnk'):
                    results.append({"shortcut": os.path.join(root, f)})
    return results[:10]


def _check_running(name: str) -> list:
    """Check if app is currently running."""
    try:
        result = subprocess.run(
            f'tasklist /FO CSV /NH | findstr /I "{name}"',
            shell=True, capture_output=True, text=True, timeout=5,
            encoding="utf-8", errors="replace"
        )
        processes = []
        for line in result.stdout.strip().split('\n'):
            parts = [p.strip('"') for p in line.split('","')]
            if len(parts) >= 2:
                processes.append({"name": parts[0], "pid": parts[1]})
        return processes
    except Exception:
        return []


def execute(name: str, **kwargs) -> dict:
    registry = _search_registry(name)
    shortcuts = _search_start_menu(name)
    running = _check_running(name)

    return {
        "query": name,
        "found_in_registry": registry,
        "found_in_start_menu": shortcuts,
        "currently_running": running,
        "is_running": len(running) > 0,
    }
