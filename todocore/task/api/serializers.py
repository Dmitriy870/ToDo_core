from common.event import EventManager, EventName
from common.kafka_producers import KafkaTopic
from common.mixins import CeleryTaskMixin
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
        serialized_data = self.to_representation(task)
        EventManager.send_event(
            event_name=f"{EventName.CREATE}task",
            model_type="Task",
            model_data=serialized_data,
            event_type="MODEL",
            entity_id=str(task.id),
            topic=KafkaTopic.MODELS_TOPIC,
        )
        return task

    def update(self, instance, validated_data):
        old_deadline = instance.deadline
        instance = super().update(instance, validated_data)
        self.reschedule_task(
            send_deadline_notification, instance.id, old_deadline, instance.deadline
        )
        serialized_data = self.to_representation(instance)
        EventManager.send_event(
            event_name=f"{EventName.UPDATE}task",
            model_type="Task",
            model_data=serialized_data,
            event_type="MODEL",
            entity_id=str(instance.id),
            topic=KafkaTopic.MODELS_TOPIC,
        )
        return instance

    def delete(self, instance):
        self.revoke_task(instance.id)
        EventManager.send_event(
            event_name=f"{EventName.DELETE}task",
            model_type="Task",
            event_type="MODEL",
            entity_id=str(instance.id),
            topic=KafkaTopic.MODELS_TOPIC,
        )
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

        serialized_data = self.to_representation(instance)
        EventManager.send_event(
            event_name=f"{EventName.UPDATE}task",
            model_type="Task",
            model_data=serialized_data,
            event_type="MODEL",
            entity_id=str(instance.id),
            topic=KafkaTopic.MODELS_TOPIC,
        )

        return instance
