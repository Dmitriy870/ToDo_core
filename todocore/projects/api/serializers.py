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
        fields = ["id", "user", "position", "role"]

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

    def update(self, instance, validated_data):
        new_role = validated_data.get("role")
        instance.role = new_role
        instance.save()
        return instance
