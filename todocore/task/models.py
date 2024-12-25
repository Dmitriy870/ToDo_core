from common.models import Base
from django.db import models


class Task(Base):
    title = models.CharField(max_length=255)
    description = models.TextField(verbose_name="Content of the task")
    deadline = models.DateTimeField()
    status = models.CharField(max_length=255)
    assignee = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="assigned_tasks"
    )
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="tasks")
    created_by = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="created_tasks"
    )

    class Meta:
        db_table = "task"

    def __str__(self):
        return self.title
