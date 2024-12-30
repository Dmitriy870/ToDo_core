from common.models import Position
from django.core.exceptions import ValidationError
from projects.models import Project, ProjectUser
from rest_framework import serializers


class ProjectCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"

    def create(self, validated_data):
        created_by = validated_data.get("created_by")
        if not created_by:
            raise ValidationError({"created_by": "This field is required."})

        project = Project.objects.create(**validated_data)
        return project

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        return instance


class ProjectPartialUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        exclude = ["created_by", "created_at"]
        extra_kwargs = {
            "title": {"required": False},
            "description": {"required": False},
            "status": {"required": False},
        }


class ProjectUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectUser
        fields = ["id", "project", "user", "position", "role"]

    def validate(self, data):
        position = data.get("position")
        if position and not Position.objects.filter(id=position.id).exists():
            raise ValidationError({"position": "Position does not exist."})

        role = data.get("role", "Reader")
        valid_roles = [role[0] for role in ProjectUser.ROLE_CHOICES]
        if role not in valid_roles:
            raise ValidationError(
                {"role": f"Invalid role. Allowed roles are: {', '.join(valid_roles)}"}
            )

        return data

    def create(self, validated_data):
        project = self.context["project"]
        user = validated_data["user"]
        role = validated_data.get("role", "Reader")
        position = validated_data["position"]

        if ProjectUser.objects.filter(project=project, user=user, position=position).exists():
            raise ValidationError(
                {"user": f"User with id {user.id} already exists with the same position"}
            )

        return ProjectUser.objects.create(project=project, user=user, position=position, role=role)


class ProjectUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectUser
        fields = ["user", "role"]

    def validate(self, data):
        new_role = data.get("role")
        valid_roles = [role[0] for role in ProjectUser.ROLE_CHOICES]
        if new_role not in valid_roles:
            raise ValidationError(
                {"role": f"Invalid role. Allowed roles are: {', '.join(valid_roles)}"}
            )
        return data

    def update(self, instance, validated_data):
        new_role = validated_data.get("role")
        instance.role = new_role
        instance.save()
        return instance
