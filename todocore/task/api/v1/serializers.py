from common.models import User
from django.core.exceptions import ValidationError
from projects.models import Project, ProjectUser
from rest_framework import serializers
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


class TaskSerializer(serializers.ModelSerializer, TaskSerializerMixin):
    class Meta:
        model = Task
        fields = "__all__"

    def validate(self, data):
        if self.instance is None:
            title = data.get("title")
            project = data.get("project")
            assignee = data.get("assignee")

            if Task.objects.filter(title=title, project=project, assignee=assignee).exists():
                raise serializers.ValidationError(
                    {"error": "Task with the same title, project, and assignee already exists."}
                )
        return self.validate_assignee_and_project(data)


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
