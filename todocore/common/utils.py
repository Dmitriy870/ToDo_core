import logging
import typing

from rest_framework.permissions import BasePermission

logger = logging.getLogger(__name__)
PermissionClass = typing.TypeVar("PermissionClass", bound=BasePermission)


class DynamicPermissionMixin:

    permission_map: dict[str, list[PermissionClass]] = {}

    def get_permissions(self):
        logger.info("Into get_permissions")
        permissions = self.permission_map.get(self.action, super().get_permissions())

        return permissions
