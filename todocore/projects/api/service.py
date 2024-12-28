from common.models import Position, User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from projects.models import Project, ProjectUser


class ProjectService:
    @staticmethod
    def get_all_projects():
        return Project.objects.all()

    @staticmethod
    def get_project_by_id(project_id):
        try:
            return Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return None

    @staticmethod
    def create_project(data):
        return Project.objects.create(**data)

    @staticmethod
    def update_project(project, data):
        for key, value in data.items():
            setattr(project, key, value)
        project.save()
        return project

    @staticmethod
    def delete_project(project):
        project.delete()

    @staticmethod
    def search_projects(filters):
        return Project.objects.filter(**filters)


class ProjectUserService:

    @staticmethod
    def add_user_on_project(project, validated_data) -> ProjectUser:
        if "user_id" not in validated_data:
            raise ValidationError({"error": "User ID is missing in validated_data"})

        user_id = validated_data["user_id"]
        role = validated_data.get("role", "Reader")
        position_uuid = validated_data["position"]

        try:
            position = Position.objects.get(id=position_uuid)
        except Position.DoesNotExist:
            raise ValidationError({"position": f"Position with id {position_uuid} does not exist."})

        valid_roles = [role[0] for role in ProjectUser.ROLE_CHOICES]
        if role not in valid_roles:
            raise ValidationError(
                {"role": f"Invalid role. Allowed roles are: {', '.join(valid_roles)}"}
            )

        user = User.objects.filter(id=user_id).first()
        if not user:
            raise ObjectDoesNotExist("User not found")

        if ProjectUser.objects.filter(project=project, user=user, position=position).exists():
            raise ValidationError(
                {"user": f"User with id {user_id} already exists with the same position"}
            )

        return ProjectUser.objects.create(project=project, user=user, position=position, role=role)

    @staticmethod
    def change_user_role_on_project(project, user, new_role="Developer") -> ProjectUser:
        valid_roles = [role[0] for role in ProjectUser.ROLE_CHOICES]
        if new_role not in valid_roles:
            raise ValidationError(
                {"role": f"Invalid role. Allowed roles are: {', '.join(valid_roles)}"}
            )

        try:
            project_user = ProjectUser.objects.get(project=project, user=user)
            project_user.role = new_role
            project_user.save()
            return project_user
        except ProjectUser.DoesNotExist:
            raise ValidationError({"error": "User is not in the project."})

    @staticmethod
    def delete_user_on_project(project, user):
        if not ProjectUser.objects.filter(project=project, user=user).exists():
            raise ValidationError({"user": f"User with id {user} does not exists"})

        return ProjectUser.objects.filter(project=project, user=user).delete()
