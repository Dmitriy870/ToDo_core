from projects.models import Project, ProjectUser
from rest_framework import serializers


class ProjectUserSerializer(serializers.Serializer):
    user_id = serializers.UUIDField(required=True)
    role = serializers.ChoiceField(choices=ProjectUser.ROLE_CHOICES, default="Reader")
    position = serializers.UUIDField(required=True)

    def validate(self, data):
        if "user_id" not in data:
            raise serializers.ValidationError({"error": "User ID is required."})
        return data


class ProjectUserUpdateSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=ProjectUser.ROLE_CHOICES, required=True)


class ProjectCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"

    def create(self, validated_data):
        try:
            created_by = validated_data.get("created_by")
            if not created_by:
                raise serializers.ValidationError({"created_by": "This field is required."})

            project = Project.objects.create(**validated_data)

            ProjectUser.objects.create(project=project, user=created_by, role="Owner")

            return project

        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})

    def update(self, instance, validated_data):
        try:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance

        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"


class ProjectPartialUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        exclude = [
            "created_by",
            "created_at",
        ]
        extra_kwargs = {
            "title": {"required": False},
            "description": {"required": False},
            "status": {"required": False},
        }


class ProjectSearchSerializer(serializers.Serializer):
    created_by = serializers.UUIDField(required=True)
    title = serializers.CharField(required=False)
    status = serializers.CharField(required=False)


class ProjectSearchSerializerOutput(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["title", "status", "created_at"]
