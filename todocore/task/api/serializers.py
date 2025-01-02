import os

from celery.result import AsyncResult
from common.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from projects.models import Project, ProjectUser
from redis import Redis
from rest_framework import serializers
from task.api.tasks import send_deadline_notification
from task.models import Task

redis_host = os.getenv("REDIS_HOST")
redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_db = int(os.getenv("REDIS_DB", 0))


class CeleryTaskMixin:
    """
    Mixin for managing Celery tasks.
    """

    redis_client = Redis(host=redis_host, port=redis_port, db=redis_db)

    def schedule_task(self, task, task_id, eta):
        """
        Schedule a Celery task and save its ID in Redis.
        """
        task_result = task.apply_async(args=[task_id], eta=eta)
        self.redis_client.set(f"task: {task_id}", task_result.id)
        return task_result

    def revoke_task(self, task_id):
        """
        Revoke a Celery task and delete its ID from Redis.
        """
        stored_task_id = self.redis_client.get(f"task : {task_id}")
        if stored_task_id:
            AsyncResult(stored_task_id.decode()).revoke()
            self.redis_client.delete(f"task: {task_id}")

    def reschedule_task(self, task, task_id, old_deadline, new_deadline):
        """
        Revoke the old task and schedule a new one if the deadline has changed.
        """
        if old_deadline != new_deadline:
            notification_time = new_deadline - timezone.timedelta(hours=1)
            self.revoke_task(task_id)
            return self.schedule_task(task, task_id, notification_time)
        return None


class TaskSerializerMixin:
    def validate_assignee_and_project(self, data):
        project = data.get("project")
        assignee = data.get("assignee")

        project_id = project.id if hasattr(project, "id") else project
        assignee_id = assignee.id if hasattr(assignee, "id") else assignee

        if project_id and assignee_id:
            if not User.objects.filter(id=assignee_id).exists():
                raise ValidationError({"assignee": "User does not exist."})

            if not Project.objects.filter(id=project_id).exists():
                raise ValidationError({"project": "Project does not exist."})

            if not ProjectUser.objects.filter(project_id=project_id, user_id=assignee_id).exists():
                raise ValidationError({"assignee": "The assignee does not belong to the project."})

        return data


class TaskSerializer(serializers.ModelSerializer, TaskSerializerMixin, CeleryTaskMixin):
    class Meta:
        model = Task
        fields = "__all__"

    def validate(self, data):
        if self.instance is None:
            title = data.get("title")
            project = data.get("project")
            assignee = data.get("assignee")

            deadline = data.get("deadline")
            if deadline < timezone.now():
                raise serializers.ValidationError({"deadline": "Deadline must be in the future."})

            if Task.objects.filter(title=title, project=project, assignee=assignee).exists():
                raise serializers.ValidationError(
                    {"error": "Task with the same title, project, and assignee already exists."}
                )
        return self.validate_assignee_and_project(data)

    def create(self, validated_data):

        task = Task.objects.create(**validated_data)
        notification_time = task.deadline - timezone.timedelta(hours=1)
        self.schedule_task(send_deadline_notification, task.id, notification_time)
        return task

    def update(self, instance, validated_data):
        old_deadline = instance.deadline
        instance = super().update(instance, validated_data)
        self.reschedule_task(
            send_deadline_notification, instance.id, old_deadline, instance.deadline
        )
        return instance

    def delete(self, instance):
        self.revoke_task(instance.id)
        instance.delete()


class TaskPartialUpdateSerializer(serializers.ModelSerializer, TaskSerializerMixin):
    class Meta:
        model = Task
        exclude = ["created_by", "created_at"]
        extra_kwargs = {
            "title": {"required": False},
            "description": {"required": False},
            "deadline": {"required": False},
            "status": {"required": False},
            "assignee": {"required": False},
            "project": {"required": False},
        }

    def validate(self, data):
        if "project" not in data:
            data.pop("project", None)
        return self.validate_assignee_and_project(data)
