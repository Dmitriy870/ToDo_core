import json
import logging
import typing
from uuid import UUID

from django.db.models import Model
from rest_framework.permissions import BasePermission

logger = logging.getLogger(__name__)
PermissionClass = typing.TypeVar("PermissionClass", bound=BasePermission)


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)

        if isinstance(obj, Model):
            return {field.name: getattr(obj, field.name) for field in obj._meta.fields}

        return super().default(obj)


class DynamicPermissionMixin:

    permission_map: dict[str, list[PermissionClass]] = {}

    def get_permissions(self):
        logger.info("Into get_permissions")
        permissions = self.permission_map.get(self.action, super().get_permissions())

        return permissions
