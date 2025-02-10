from common.pagination import StandardResultsSetPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from task.api.permissions import HasTaskRole, IsAssignee
from task.api.serializers import TaskPartialUpdateSerializer, TaskSerializer
from task.api.v1.filters import TaskFilter
from task.models import Task


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    filterset_class = TaskFilter
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ["created_at", "title"]
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        permission_map = {
            "create": [HasTaskRole(["Developer", "Maintainer", "Owner"])],
            "update": [HasTaskRole(["Developer", "Maintainer", "Owner"]), IsAssignee()],
            "partial_update": [
                HasTaskRole(["Developer", "Maintainer", "Owner"]),
                IsAssignee(),
            ],
            "destroy": [HasTaskRole(["Owner"])],
        }
        return permission_map.get(self.action, super().get_permissions())

    def get_serializer_class(self):
        if self.action == "partial_update":
            return TaskPartialUpdateSerializer
        return TaskSerializer
