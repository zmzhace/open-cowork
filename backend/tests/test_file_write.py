import pytest
import tempfile
import os
from src.tools.file_write import FileWriteTool


@pytest.mark.asyncio
async def test_file_write_tool():
    """Test file write tool"""
    temp_path = tempfile.mktemp()

    try:
        tool = FileWriteTool()
        await tool.execute(path=temp_path, content="Test content")

        with open(temp_path, 'r') as f:
            assert f.read() == "Test content"
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
