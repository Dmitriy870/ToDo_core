from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ProjectSearchViewSet, ProjectUserViewSet, ProjectViewSet

router = DefaultRouter()
router.register(r"project", ProjectViewSet, basename="project")

project_user_urls = [
    path(
        "project/<uuid:project_pk>/users/",
        ProjectUserViewSet.as_view({"post": "add_user"}),
        name="project-add-user",
    ),
    path(
        "project/<uuid:project_pk>/users/<uuid:user_id>/",
        ProjectUserViewSet.as_view({"patch": "update_user_role", "delete": "delete_user"}),
        name="project-update-user-role-or-delete-user",
    ),
]

project_search_url = [
    path(
        "api/v1/project/",
        ProjectSearchViewSet.as_view({"get": "list"}),
        name="project-search",
    ),
]


urlpatterns = [
    path("", include(router.urls)),
    path("", include(project_user_urls)),
    path("", include(project_search_url)),
]
