import importlib
import platform
import sys

import pytest


UNSUPPORTED_MESSAGE = "Error: WeChat automation is only supported on Windows."



def _clear_tools_modules():
    for module_name in [
        "src.tools.wechat_control",
        "src.tools",
    ]:
        sys.modules.pop(module_name, None)



def _import_under_darwin(monkeypatch, module_name: str):
    _clear_tools_modules()
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    return importlib.import_module(module_name)



def test_wechat_control_import_is_safe_on_non_windows(monkeypatch):
    module = _import_under_darwin(monkeypatch, "src.tools.wechat_control")

    assert module.IS_WINDOWS is False
    assert module.user32 is None



def test_wechat_control_helpers_fail_clearly_on_non_windows(monkeypatch):
    module = _import_under_darwin(monkeypatch, "src.tools.wechat_control")

    with pytest.raises(RuntimeError, match="only supported on Windows"):
        module.find_window_by_title("微信")

    with pytest.raises(RuntimeError, match="only supported on Windows"):
        module.activate_window(123)



@pytest.mark.asyncio
async def test_wechat_tool_execute_returns_unsupported_message_on_non_windows(monkeypatch):
    module = _import_under_darwin(monkeypatch, "src.tools.wechat_control")

    tool = module.WeChatSendMessageTool()

    result = await tool.execute(contact_name="Alice", message="hello")

    assert result == UNSUPPORTED_MESSAGE



def test_tools_package_import_is_safe_on_non_windows(monkeypatch):
    module = _import_under_darwin(monkeypatch, "src.tools")

    assert module.WeChatSendMessageTool is not None
    assert module.WeChatSendMessageTool().name == "wechat_send_message"
