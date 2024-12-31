from common.models import Base
from django.db import models


class Project(Base):
    title = models.CharField(max_length=55)
    description = models.TextField()
    status = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        "common.User", on_delete=models.CASCADE, related_name="created_projects"
    )

    class Meta:
        db_table = "project"


class ProjectUser(Base):
    ROLE_CHOICES = [
        ("Reader", "Reader"),
        ("Developer", "Developer"),
        ("Maintainer", "Maintainer"),
        ("Owner", "Owner"),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="project_users")
    user = models.ForeignKey("common.User", on_delete=models.CASCADE, related_name="user_projects")
    position = models.ForeignKey(
        "common.Position", on_delete=models.CASCADE, related_name="project_users"
    )
    role = models.CharField(max_length=100, choices=ROLE_CHOICES)
    is_blocked = models.BooleanField(default=False)
    blocked_by = models.ForeignKey(
        "common.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="blocked_users",
    )

    class Meta:
        db_table = "project_user"
