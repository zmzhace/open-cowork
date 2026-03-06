from typing import Dict, Set


class PermissionManager:
    """Manage file and operation permissions"""

    def __init__(self):
        self._permissions: Dict[str, Set[str]] = {}

    def grant_permission(self, path: str, access_level: str):
        """Grant permission for a path"""
        if path not in self._permissions:
            self._permissions[path] = set()
        self._permissions[path].add(access_level)

    def revoke_permission(self, path: str, access_level: str):
        """Revoke permission for a path"""
        if path in self._permissions:
            self._permissions[path].discard(access_level)

    def check_permission(self, path: str, access_level: str) -> bool:
        """Check if permission is granted"""
        return path in self._permissions and access_level in self._permissions[path]

    def list_permissions(self) -> Dict[str, Set[str]]:
        """List all permissions"""
        return self._permissions.copy()
