from common.event import EventManager, EventName
from common.kafka_producers import KafkaTopic
from common.permissions import IsAdmin
from common.utils import DynamicPermissionMixin, PermissionClass
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from projects.api.permissions import HasProjectRole, IsProjectOwner
from projects.api.serializers import (
    ProjectCreateUpdateSerializer,
    ProjectPartialUpdateSerializer,
    ProjectUserSerializer,
    ProjectUserUpdateSerializer,
)
from projects.api.v1.filters import ProjectFilter
from projects.models import Project, ProjectUser
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response


class ProjectViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    DynamicPermissionMixin,
    viewsets.GenericViewSet,
):
    queryset = Project.objects.all()
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = ProjectFilter
    lookup_field = "id"

    def get_serializer_class(self):
        if self.action in ["update", "partial_update"]:
            return ProjectPartialUpdateSerializer
        return ProjectCreateUpdateSerializer

    permission_map: dict[str, list[PermissionClass]] = {
        "create": [IsAdmin()],
        "update": [IsProjectOwner()],
        "partial_update": [IsProjectOwner()],
        "destroy": [IsAdmin()],
    }

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        instance = self.get_object()
        EventManager.send_event(
            model_type="Project",
            event_name=f"{EventName.GET}project",
            event_type="MODEL",
            entity_id=str(instance.id),
            model_data=response.data,
            topic=KafkaTopic.EVENTS_TOPIC,
        )
        return response

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        EventManager.send_event(
            event_name=f"{EventName.GET_ALL}projects",
            model_type="Project",
            event_type="MODEL",
            topic=KafkaTopic.MODELS_TOPIC,
        )
        return response

    def perform_destroy(self, instance):

        EventManager.send_event(
            event_name=f"{EventName.DELETE}project",
            model_type="Project",
            event_type="MODEL",
            entity_id=str(instance.id),
            topic=KafkaTopic.MODELS_TOPIC,
        )
        instance.delete()


class ProjectUserViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    DynamicPermissionMixin,
    viewsets.GenericViewSet,
):
    queryset = ProjectUser.objects.all()

    def get_serializer_class(self):
        if self.action in ["update", "partial_update", "update_user_role"]:
            return ProjectUserUpdateSerializer
        return ProjectUserSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        project_pk = self.kwargs.get("project_pk")
        project = get_object_or_404(Project, id=project_pk)
        context["project"] = project
        return context

    def get_object(self):
        project_pk = self.kwargs.get("project_pk")

        user_id = (
            self.kwargs.get("user_id")
            or self.request.data.get("user")
            or self.request.data.get("user_id")
        )

        if not user_id:
            raise ValidationError({"user": "User ID is required."})

        try:
            return ProjectUser.objects.get(project__id=project_pk, user__id=user_id)
        except ProjectUser.DoesNotExist:
            raise ObjectDoesNotExist("ProjectUser not found")

    permission_map: dict[str, list[PermissionClass]] = {
        "add_user": [HasProjectRole(["Maintainer", "Owner"])],
        "update_user_role": [HasProjectRole(["Maintainer", "Owner"])],
        "delete_user": [IsProjectOwner()],
    }

    def perform_destroy(self, instance):

        EventManager.send_event(
            event_name=f"{EventName.DELETE_FROM_PROJECT}",
            model_type="ProjectUser",
            event_type="EVENT",
            entity_id=str(instance.id),
            topic=KafkaTopic.EVENTS_TOPIC,
        )
        instance.delete()

    @action(detail=False, methods=["post"], url_path="project/(?P<project_pk>[^/.]+)/users")
    def add_user(self, request, *args, **kwargs):
        try:
            return self.create(request, *args, **kwargs)
        except (ObjectDoesNotExist, ValidationError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["patch"], url_path="project/(?P<project_pk>[^/.]+)/users")
    def update_user_role(self, request, *args, **kwargs):
        try:
            return self.partial_update(request, *args, **kwargs)
        except (ObjectDoesNotExist, ValidationError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=["delete"],
        url_path="project/(?P<project_pk>[^/.]+)/users/(?P<user_id>[^/.]+)",
    )
    def delete_user(self, request, *args, **kwargs):
        try:
            return self.destroy(request, *args, **kwargs)
        except (ObjectDoesNotExist, ValidationError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
