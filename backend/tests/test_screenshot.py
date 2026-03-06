import pytest
from unittest.mock import patch, MagicMock
from src.tools.screenshot import ScreenshotTool


@pytest.mark.asyncio
async def test_screenshot_tool():
    """Test screenshot tool"""
    with patch('src.tools.screenshot.mss') as mock_mss:
        mock_sct = MagicMock()
        mock_mss.mss.return_value.__enter__.return_value = mock_sct
        mock_sct.shot.return_value = "/tmp/screenshot.png"

        tool = ScreenshotTool()
        result = await tool.execute()

        assert "screenshot.png" in result
