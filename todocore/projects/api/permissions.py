import logging

from projects.models import Project, ProjectUser
from rest_framework.permissions import BasePermission

logger = logging.getLogger(__name__)


class ProjectRolePermission(BasePermission):
    allowed_roles = []

    def has_permission(self, request, view):
        if getattr(request, "role", None) == "admin":
            return True

        project_pk = view.kwargs.get("project_pk") or view.kwargs.get("id")
        if not project_pk:
            logger.info("No project_pk found in URL")
            return False

        try:
            project_user = ProjectUser.objects.get(project_id=project_pk, user_id=request.user_id)
            logger.info(
                f"has_permission: user={request.user.id}, project_pk={project_pk}, "
                f"user_role={project_user.role}, allowed_roles={self.allowed_roles}"
            )
            return project_user.role in self.allowed_roles
        except ProjectUser.DoesNotExist:
            logger.info(
                f"User {request.user_id} tried to request the project, but does not have access"
            )
            return False

    def has_object_permission(self, request, view, obj):
        if getattr(request, "role", None) == "admin":
            return True

        if isinstance(obj, Project):
            project_id = obj.id
        else:
            project_id = getattr(obj, "project_id", None)

        if not project_id:
            logger.info(f"User {request.user_id} has no project reference")
            return False

        try:
            project_user = ProjectUser.objects.get(project_id=project_id, user_id=request.user_id)
            logger.info(
                f"has_object_permission: user={request.user.id}, project_id={project_id}, "
                f"user_role={project_user.role}, allowed_roles={self.allowed_roles}"
            )
            return project_user.role in self.allowed_roles
        except ProjectUser.DoesNotExist:
            logger.info("User is not associated with this project")
            return False


class IsProjectOwner(ProjectRolePermission):
    def __init__(self):
        super().__init__()
        self.allowed_roles = ["Owner"]


class HasProjectRole(ProjectRolePermission):
    def __init__(self, allowed_roles):
        super().__init__()
        self.allowed_roles = allowed_roles
