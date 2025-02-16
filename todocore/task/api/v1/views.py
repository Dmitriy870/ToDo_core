from common.pagination import StandardResultsSetPagination
from common.utils import DynamicPermissionMixin, PermissionClass
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from task.api.permissions import HasTaskRole, IsAssignee
from task.api.serializers import TaskPartialUpdateSerializer, TaskSerializer
from task.api.v1.filters import TaskFilter
from task.models import Task


class TaskViewSet(DynamicPermissionMixin, viewsets.ModelViewSet):
    queryset = Task.objects.all()
    filterset_class = TaskFilter
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ["created_at", "title"]
    pagination_class = StandardResultsSetPagination

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
        return TaskSerializer
