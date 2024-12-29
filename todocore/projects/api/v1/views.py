from common.models import User
from common.pagination import StandardResultsSetPagination
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from projects.api.service import ProjectService, ProjectUserService
from projects.api.v1.serializers import (
    ProjectCreateUpdateSerializer,
    ProjectPartialUpdateSerializer,
    ProjectSearchSerializer,
    ProjectSearchSerializerOutput,
    ProjectSerializer,
    ProjectUserSerializer,
    ProjectUserUpdateSerializer,
)
from projects.models import Project
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.action in ["create", "update"]:
            return ProjectCreateUpdateSerializer
        elif self.action == "partial_update":
            return ProjectPartialUpdateSerializer
        return ProjectSerializer

    def retrieve(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        if pk is None:
            raise ValidationError("No primary key provided")
        project = ProjectService.get_project_by_id(pk)
        if not project:
            raise ObjectDoesNotExist("Project not found")
        serializer = ProjectSerializer(project)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            project = ProjectService.create_project(serializer.validated_data)
            return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)
        raise ValidationError(serializer.errors)

    def update(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        if pk is None:
            raise ValidationError("No primary key provided")
        project = ProjectService.get_project_by_id(pk)
        if not project:
            raise ObjectDoesNotExist("Project not found")
        serializer = self.get_serializer(project, data=request.data)
        if serializer.is_valid():
            updated_project = ProjectService.update_project(project, serializer.validated_data)
            return Response(ProjectSerializer(updated_project).data)
        raise ValidationError(serializer.errors)

    def partial_update(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        if pk is None:
            raise ValidationError("No primary key provided")
        project = ProjectService.get_project_by_id(pk)
        if not project:
            raise ObjectDoesNotExist("Project not found")
        serializer = self.get_serializer(project, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            updated_project = ProjectService.update_project(project, serializer.validated_data)
            return Response(ProjectSerializer(updated_project).data)
        raise ValidationError(serializer.errors)

    def destroy(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        if pk is None:
            raise ValidationError("No primary key provided")
        project = ProjectService.get_project_by_id(pk)
        if not project:
            raise ObjectDoesNotExist("Project not found")
        ProjectService.delete_project(project)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectUserViewSet(viewsets.GenericViewSet):

    def get_serializer_class(self):
        if self.action == "add_user":
            return ProjectUserSerializer
        elif self.action == "update_user_role":
            return ProjectUserUpdateSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=["post"], url_path="project/(?P<project_pk>[^/.]+)/users")
    def add_user(self, request, *args, **kwargs):
        project_pk = kwargs.get("project_pk")
        if not project_pk:
            raise ValidationError({"error": "No project primary key provided."})

        project = ProjectService.get_project_by_id(project_pk)
        if not project:
            raise ObjectDoesNotExist({"error": "Project not found."})

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            ProjectUserService.add_user_on_project(project, serializer.validated_data)
            return Response({"message": "User added to project"}, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({"error": e}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["patch"], url_path="(?P<user_id>[^/.]+)")
    def update_user_role(self, request, project_pk=None, user_id=None):
        project = ProjectService.get_project_by_id(project_pk)
        if not project:
            raise ObjectDoesNotExist("Project not found")
        user = User.objects.filter(id=user_id).first()
        if not user:
            raise ObjectDoesNotExist("User not found")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_role = serializer.validated_data.get("role")
        ProjectUserService.change_user_role_on_project(project, user, new_role)
        return Response({"message": "User role updated"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["delete"], url_path="(?P<user_id>[^/.]+)")
    def delete_user(self, request, *args, **kwargs):
        project_pk = kwargs.get("project_pk")
        if not project_pk:
            raise ValidationError("No project primary key provided")
        user_id = kwargs.get("user_id")
        if not user_id:
            raise ValidationError("No user id provided")
        project = ProjectService.get_project_by_id(project_pk)
        if not project:
            raise ObjectDoesNotExist("Project not found")
        user = User.objects.filter(id=user_id).first()
        if not user:
            raise ObjectDoesNotExist("User not found")

        ProjectUserService.delete_user_on_project(project, user)
        return Response({"message": "User removed from project"}, status=status.HTTP_204_NO_CONTENT)


class ProjectSearchViewSet(viewsets.GenericViewSet):
    serializer_class = ProjectSearchSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "created_by",
                openapi.IN_QUERY,
                description="User id, создавшего проект",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "title",
                openapi.IN_QUERY,
                description="Название проекта",
                type=openapi.TYPE_STRING,
                required=False,
            ),
            openapi.Parameter(
                "status",
                openapi.IN_QUERY,
                description="Статус проекта",
                type=openapi.TYPE_STRING,
                required=False,
            ),
        ]
    )
    def list(self, request):
        search_params = request.query_params.dict()
        search_serializer = ProjectSearchSerializer(data=search_params)
        if not search_serializer.is_valid():
            raise ValidationError(search_serializer.errors)

        filters = search_serializer.validated_data
        user_id = filters.get("created_by")
        user = User.objects.filter(id=user_id).first()
        if not user:
            raise ObjectDoesNotExist("User not found")

        projects = ProjectService.search_projects(filters)
        serializer = ProjectSearchSerializerOutput(projects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
