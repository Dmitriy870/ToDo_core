import django_filters
from task.models import Task


class TaskFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr="icontains")
    status = django_filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = Task
        fields = ["title", "status"]
