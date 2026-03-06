import pytest
from src.permissions import PermissionManager


def test_permission_check():
    """Test permission checking"""
    pm = PermissionManager()

    # No permission granted
    assert not pm.check_permission("/test/file.txt", "read")

    # Grant permission
    pm.grant_permission("/test/file.txt", "read")
    assert pm.check_permission("/test/file.txt", "read")

    # Check write permission (not granted)
    assert not pm.check_permission("/test/file.txt", "write")
