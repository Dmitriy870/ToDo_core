from common.mixins.celery_mixin import CeleryTaskMixin
from common.mixins.file_mixin import FileUploadMixin
from common.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from projects.models import Project, ProjectUser
from rest_framework import serializers
from task.api.tasks import send_deadline_notification
from task.models import Task


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


class TaskSerializer(TaskSerializerMixin, CeleryTaskMixin, serializers.ModelSerializer):
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


class TaskPartialUpdateSerializer(
    TaskSerializerMixin, CeleryTaskMixin, serializers.ModelSerializer
):
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

    def update(self, instance, validated_data):
        old_deadline = instance.deadline
        instance = super().update(instance, validated_data)

        if "deadline" in validated_data and old_deadline != instance.deadline:
            self.reschedule_task(
                send_deadline_notification, instance.id, old_deadline, instance.deadline
            )
        return instance


class TaskFilesUpdateSerializer(FileUploadMixin, serializers.ModelSerializer):
    files = serializers.ListField(child=serializers.FileField(), required=True, write_only=True)

    class Meta:
        model = Task
        fields = ("files", "file_slugs")
        extra_kwargs = {"file_slugs": {"read_only": True}}

    def update(self, instance, validated_data):
        self.slugs_field_name = "file_slugs"
        self.file_field_name = "files"
        return self.update_file_field(instance, validated_data)
