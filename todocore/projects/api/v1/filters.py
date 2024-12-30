import django_filters
from projects.models import Project


class ProjectFilter(django_filters.FilterSet):
    created_by = django_filters.UUIDFilter(field_name="created_by")
    title = django_filters.CharFilter(field_name="title", lookup_expr="icontains")
    status = django_filters.CharFilter(field_name="status", lookup_expr="icontains")

    class Meta:
        model = Project
        fields = ["created_by", "title", "status"]
