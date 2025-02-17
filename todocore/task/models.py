from enum import Enum

from common.models import Base
from django.contrib.postgres.fields import ArrayField
from django.db import models


class TaskTypeCelery(Enum):
    SEND_MAIL = "send_mail"
    OTHER_TYPE = "other_type"


class Task(Base):
    title = models.CharField(max_length=255)
    description = models.TextField(verbose_name="Content of the task")
    deadline = models.DateTimeField()
    status = models.CharField(max_length=255)
    assignee = models.ForeignKey(
        "common.User", on_delete=models.CASCADE, related_name="assigned_tasks"
    )
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="task")
    file_slugs = ArrayField(
        models.CharField(max_length=255, blank=True),
        blank=True,
        default=list,
        verbose_name="File slugs",
    )
    created_by = models.ForeignKey(
        "common.User", on_delete=models.CASCADE, related_name="created_tasks"
    )

    class Meta:
        db_table = "task"

    def __str__(self):
        return self.title
