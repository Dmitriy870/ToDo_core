from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return getattr(request, "role", None) == "admin"


class IsUser(BasePermission):
    def has_permission(self, request, view):
        return getattr(request, "role", None) == "user"
