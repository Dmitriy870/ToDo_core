from common.pagination import StandardResultsSetPagination
from common.utils import DynamicPermissionMixin, PermissionClass
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from task.api.permissions import HasTaskRole, IsAssignee
from task.api.serializers import (
    TaskFilesUpdateSerializer,
    TaskPartialUpdateSerializer,
    TaskSerializer,
)
from task.api.v1.filters import TaskFilter
from task.models import Task


class TaskViewSet(DynamicPermissionMixin, viewsets.ModelViewSet):
    queryset = Task.objects.all()
    filterset_class = TaskFilter
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ["created_at", "title"]
    pagination_class = StandardResultsSetPagination
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    permission_map: dict[str, list[PermissionClass]] = {
        "create": [HasTaskRole(["Developer", "Maintainer", "Owner"])],
        "update": [HasTaskRole(["Developer", "Maintainer", "Owner"]), IsAssignee()],
        "partial_update": [
            HasTaskRole(["Developer", "Maintainer", "Owner"]),
            IsAssignee(),
        ],
        "destroy": [HasTaskRole(["Owner"])],
    }

    def get_serializer_class(self):
        if self.action == "partial_update":
            return TaskPartialUpdateSerializer
        if self.action == "upload_files":
            return TaskFilesUpdateSerializer
        return TaskSerializer

    @action(
        methods=["patch"],
        detail=True,
        url_path="files",
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload_files(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
