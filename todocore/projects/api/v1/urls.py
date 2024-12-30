from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ProjectUserViewSet, ProjectViewSet

router = DefaultRouter()
router.register(r"project", ProjectViewSet, basename="project")

project_user_urls = [
    path(
        "project/<uuid:project_pk>/users/",
        ProjectUserViewSet.as_view({"post": "add_user", "patch": "update_user_role"}),
        name="project-add-or-update-user",
    ),
    path(
        "project/<uuid:project_pk>/users/<uuid:user_id>/",
        ProjectUserViewSet.as_view({"delete": "delete_user"}),
        name="project-delete-user",
    ),
]

urlpatterns = [
    path("", include(router.urls)),
    path("", include(project_user_urls)),
]
