from common.pagination import StandardResultsSetPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from task.api.serializers import TaskPartialUpdateSerializer, TaskSerializer
from task.models import Task

from .filters import TaskFilter


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    filterset_class = TaskFilter
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ["created_at", "title"]
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.action == "partial_update":
            return TaskPartialUpdateSerializer
        return TaskSerializer
