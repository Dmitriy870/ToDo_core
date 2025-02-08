from common.event import EventManager, EventName
from common.kafka_producers import KafkaTopic
from projects.models import Project, ProjectUser
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class ProjectCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"

    def create(self, validated_data):
        created_by = validated_data.get("created_by")
        title = validated_data.get("title")
        if not created_by:
            raise ValidationError({"created_by": "This field is required."})
        if Project.objects.filter(title=title, created_by=created_by).exists():
            raise ValidationError({"user": f"Project with title {title} already exists."})

        project = Project.objects.create(**validated_data)

        serialized_data = self.to_representation(project)

        EventManager.send_event(
            event_name=f"{EventName.CREATE.value}project",
            model_type="Project",
            model_data=serialized_data,
            entity_id=str(project.id),
            topic=KafkaTopic.MODELS_TOPIC.value,
        )

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

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)

        serialized_data = self.to_representation(instance)
        EventManager.send_event(
            event_name=f"{EventName.UPDATE.value}project",
            model_type="Project",
            model_data=serialized_data,
            entity_id=str(instance.id),
            topic=KafkaTopic.MODELS_TOPIC.value,
        )

        return instance


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

        instance = ProjectUser.objects.create(
            project=project, user=user, position=position, role=role
        )

        serialized_data = self.to_representation(instance)

        EventManager.send_event(
            event_name=f"{EventName.ADD_ON_PROJECT.value}",
            model_type="ProjectUser",
            model_data=serialized_data,
            entity_id=str(instance.id),
            topic=KafkaTopic.EVENTS_TOPIC.value,
        )

        return instance


class ProjectUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectUser
        fields = ["user", "role"]

    def update(self, instance, validated_data):
        new_role = validated_data.get("role")
        instance.role = new_role
        instance.save()

        EventManager.send_event(
            event_name=f"{EventName.CHANGE_ROLE_ON_PROJECT.value}",
            model_type="ProjectUser",
            entity_id=str(instance.id),
            topic=KafkaTopic.EVENTS_TOPIC.value,
        )

        return instance
