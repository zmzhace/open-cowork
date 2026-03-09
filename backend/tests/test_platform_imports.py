import importlib
import platform
import sys


def _clear_tools_modules():
    for module_name in [
        "src.tools.wechat_control",
        "src.tools",
    ]:
        sys.modules.pop(module_name, None)



def test_wechat_control_import_is_safe_on_non_windows(monkeypatch):
    _clear_tools_modules()
    monkeypatch.setattr(platform, "system", lambda: "Darwin")

    module = importlib.import_module("src.tools.wechat_control")

    assert module is not None



def test_tools_package_import_is_safe_on_non_windows(monkeypatch):
    _clear_tools_modules()
    monkeypatch.setattr(platform, "system", lambda: "Darwin")

    module = importlib.import_module("src.tools")

    assert module is not None
