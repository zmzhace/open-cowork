import pytest
import tempfile
import os
from src.tools.file_read import FileReadTool


@pytest.mark.asyncio
async def test_file_read_tool():
    """Test file read tool"""
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Hello World")
        temp_path = f.name

    try:
        tool = FileReadTool()
        result = await tool.execute(path=temp_path)

        assert result == "Hello World"
    finally:
        os.unlink(temp_path)
