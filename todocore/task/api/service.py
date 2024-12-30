from django.core.exceptions import ValidationError
from rest_framework.exceptions import NotFound
from task.models import Task


class TaskService:
    @staticmethod
    def is_exist(data):
        project = data.get("project")
        project_id = project.id if hasattr(project, "id") else project
        if not project_id:
            raise ValidationError("project_id is required")
        title = data.get("title")
        if not title:
            raise ValidationError("title is required")
        return Task.objects.filter(project_id=project_id, title=title).exists()

    @staticmethod
    def get_all_tasks():
        return Task.objects.all()

    @staticmethod
    def get_task_by_id(task_id):
        try:
            return Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            raise NotFound("Task not found.")

    @staticmethod
    def create_task(data):
        try:
            is_exist = TaskService.is_exist(data)
            if is_exist:
                raise ValidationError("Task with this title on this project already exists.")
            return Task.objects.create(**data)
        except Exception as e:
            raise ValidationError({"error": str(e)})

    @staticmethod
    def update_task(task, data):
        try:
            for attr, value in data.items():
                setattr(task, attr, value)
            task.save()
            return task
        except Exception as e:
            raise ValidationError({"error": str(e)})

    @staticmethod
    def delete_task(task):
        try:
            task.delete()
        except Task.DoesNotExist:
            raise NotFound("Task not found.")
