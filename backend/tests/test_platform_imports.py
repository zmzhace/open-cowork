import importlib
import platform
import sys

import pytest


MODULE_NAME = "src.tools.wechat_control"
UNSUPPORTED_MESSAGE = "Error: WeChat automation is only supported on Windows."


def _reload_wechat_control(monkeypatch, system_name: str):
    sys.modules.pop(MODULE_NAME, None)
    monkeypatch.setattr(platform, "system", lambda: system_name)
    return importlib.import_module(MODULE_NAME)


def test_wechat_control_import_is_safe_on_non_windows(monkeypatch):
    module = _reload_wechat_control(monkeypatch, "Darwin")

    assert module.IS_WINDOWS is False
    assert module.user32 is None


@pytest.mark.asyncio
async def test_wechat_tool_returns_clear_error_on_non_windows(monkeypatch):
    module = _reload_wechat_control(monkeypatch, "Darwin")
    tool = module.WeChatSendMessageTool()

    result = await tool.execute(contact_name="Alice", message="hello")

    assert result == UNSUPPORTED_MESSAGE
