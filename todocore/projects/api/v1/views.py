from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
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
from rest_framework.response import Response


class ProjectViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
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


class ProjectUserViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
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

        # Получаем user_id из kwargs (для DELETE) или из request.data (для POST/PATCH)
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
