import importlib
import platform
import sys

import pytest


MODULE_NAME = "src.agent.mcp_client"


def _reload_mcp_client(monkeypatch, system_name: str):
    sys.modules.pop(MODULE_NAME, None)
    monkeypatch.setattr(platform, "system", lambda: system_name)
    return importlib.import_module(MODULE_NAME)


@pytest.mark.asyncio
async def test_mcp_client_connect_is_noop_on_non_windows(monkeypatch):
    module = _reload_mcp_client(monkeypatch, "Darwin")
    client = module.WindowsMCPClient()

    await client.connect()

    assert client.session is None
    assert client.tools_cache == []


@pytest.mark.asyncio
async def test_mcp_client_get_tools_is_empty_on_non_windows(monkeypatch):
    module = _reload_mcp_client(monkeypatch, "Darwin")
    client = module.WindowsMCPClient()

    await client.connect()

    assert await client.get_tools() == []
