import logging

from projects.models import ProjectUser
from rest_framework.permissions import BasePermission

logger = logging.getLogger(__name__)


class TaskRolePermission(BasePermission):
    allowed_roles = []

    def has_permission(self, request, view):
        if getattr(request, "role", None) == "admin":
            return True

        if view.action == "list":
            logger.info("Allowing list of tasks (or add logic if needed)")
            return True

        if view.action == "create":
            project_id = request.data.get("project", None)
            if not project_id:
                logger.info("No project provided in create")
                return False

            try:
                project_user = ProjectUser.objects.get(
                    project_id=project_id, user_id=request.user_id
                )
                logger.info(
                    f"has_permission(create): user={request.user.id}, project_id={project_id}, "
                    f"user_role={project_user.role}, allowed_roles={self.allowed_roles}"
                )
                return project_user.role in self.allowed_roles
            except ProjectUser.DoesNotExist:
                logger.info(f"User {request.user.id} is not associated with this project (create)")
                return False

        logger.info("has_permission default pass")
        return True

    def has_object_permission(self, request, view, obj):
        if getattr(request, "role", None) == "admin":
            return True

        try:
            project_user = ProjectUser.objects.get(project=obj.project, user_id=request.user_id)
            logger.info(f"Allowed_roles : {self.allowed_roles}")
            if project_user.role in self.allowed_roles:
                logger.info(f"Access granted for role: {project_user.role}")
                return True
        except ProjectUser.DoesNotExist:
            logger.info(f"User {request.user_id} is not associated with the project")

        return False


class IsAssignee(TaskRolePermission):
    def has_object_permission(self, request, view, obj):
        if super().has_object_permission(request, view, obj):
            return True

        if obj.assignee_id == request.user.id:
            logger.info("User is the assignee of the task")
            return True

        logger.info("User is not the assignee of the task")
        return False


class HasTaskRole(TaskRolePermission):
    def __init__(self, allowed_roles):
        super().__init__()
        self.allowed_roles = allowed_roles
