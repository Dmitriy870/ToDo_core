from unittest.mock import patch

import pytest
from common.permissions import IsAdmin
from django.urls import reverse
from projects.api.permissions import HasProjectRole, IsProjectOwner
from projects.models import Project, ProjectUser
from rest_framework import status


@pytest.mark.django_db
class TestProjects:
    @pytest.mark.parametrize(
        "is_admin, expected_status",
        [
            (True, status.HTTP_201_CREATED),
            (False, status.HTTP_403_FORBIDDEN),
        ],
    )
    def test_create_project(
        self,
        api_client,
        user_dev,
        is_admin,
        expected_status,
        mock_request_role,
        mock_is_project_owner,
    ):
        api_client.force_authenticate(user=user_dev)

        url = reverse("project-list")
        data = {
            "title": "Test Project in Project",
            "description": "Test Project description",
            "status": "in progress",
            "created_by": user_dev.id,
        }

        with patch.object(
            IsProjectOwner,
            "has_permission",
            side_effect=lambda request, view: request.role == "admin",
        ):
            response = api_client.post(url, data=data, format="json")

        resp_json = response.json()
        assert response.status_code == expected_status, resp_json

        if expected_status == status.HTTP_201_CREATED:
            assert Project.objects.count() == 1
            assert resp_json["title"] == "Test Project in Project"
        else:
            assert Project.objects.count() == 0

    @pytest.mark.parametrize(
        "is_admin, is_owner, expected_status",
        [
            (True, True, status.HTTP_200_OK),
            (False, True, status.HTTP_200_OK),
            (True, False, status.HTTP_200_OK),
            (False, False, status.HTTP_200_OK),
        ],
    )
    def test_retrieve_project(
        self, api_client, user_dev, project, is_admin, is_owner, expected_status, mock_request_role
    ):
        api_client.force_authenticate(user=user_dev)
        url = reverse("project-detail", kwargs={"id": project.id})

        with patch.object(
            IsProjectOwner,
            "has_permission",
            side_effect=lambda request, view: request.role == "admin" or is_owner,
        ):
            response = api_client.get(url)

        resp_json = response.json()
        assert response.status_code == expected_status, resp_json
        if expected_status == status.HTTP_200_OK:
            assert resp_json["title"] == "Test Project in Project"

    def test_list_projects(self, api_client, user_dev, project, mock_request_role):
        Project.objects.create(
            title="Another Project",
            description="Another description",
            status="in progress",
            created_by=user_dev,
        )
        api_client.force_authenticate(user=user_dev)
        url = reverse("project-list")
        with patch.object(IsProjectOwner, "has_permission", side_effect=lambda request, view: True):
            response = api_client.get(url)

        resp_json = response.json()
        assert response.status_code == status.HTTP_200_OK, resp_json
        assert len(resp_json) == 2
        titles = [proj["title"] for proj in resp_json]
        assert "Test Project in Project" in titles

    @pytest.mark.parametrize(
        "is_admin, is_owner, expected_status",
        [
            (True, True, status.HTTP_200_OK),
            (False, True, status.HTTP_200_OK),
            (True, False, status.HTTP_200_OK),
            (False, False, status.HTTP_403_FORBIDDEN),
        ],
    )
    def test_update_project(
        self, api_client, user_dev, project, is_admin, is_owner, expected_status, mock_request_role
    ):
        api_client.force_authenticate(user=user_dev)
        url = reverse("project-detail", kwargs={"id": project.id})
        data = {
            "title": "Updated Project",
            "description": "Updated description",
            "status": "completed",
        }

        with patch.object(
            IsProjectOwner,
            "has_permission",
            side_effect=lambda request, view: request.role == "admin" or is_owner,
        ):
            response = api_client.put(url, data=data, format="json")

        resp_json = response.json()
        assert response.status_code == expected_status, resp_json
        if expected_status == status.HTTP_200_OK:
            assert resp_json["title"] == "Updated Project"

    @pytest.mark.parametrize(
        "is_admin, is_owner, expected_status",
        [
            (True, True, status.HTTP_200_OK),
            (False, True, status.HTTP_200_OK),
            (True, False, status.HTTP_200_OK),
            (False, False, status.HTTP_403_FORBIDDEN),
        ],
    )
    def test_partial_update_project(
        self, api_client, user_dev, project, is_admin, is_owner, expected_status, mock_request_role
    ):
        api_client.force_authenticate(user=user_dev)
        url = reverse("project-detail", kwargs={"id": project.id})
        data = {"description": "Partially updated description"}

        with patch.object(
            IsProjectOwner,
            "has_permission",
            side_effect=lambda request, view: request.role == "admin" or is_owner,
        ):
            response = api_client.patch(url, data=data, format="json")

        resp_json = response.json()
        assert response.status_code == expected_status, resp_json
        if expected_status == status.HTTP_200_OK:
            assert resp_json["description"] == "Partially updated description"

    @pytest.mark.parametrize(
        "is_admin, is_owner, expected_status",
        [
            (True, True, status.HTTP_204_NO_CONTENT),
            (False, True, status.HTTP_204_NO_CONTENT),
            (True, False, status.HTTP_204_NO_CONTENT),
            (False, False, status.HTTP_403_FORBIDDEN),
        ],
    )
    def test_delete_project(
        self, api_client, user_dev, project, is_admin, is_owner, expected_status, mock_request_role
    ):
        api_client.force_authenticate(user=user_dev)
        url = reverse("project-detail", kwargs={"id": project.id})

        with patch.object(
            IsProjectOwner,
            "has_permission",
            side_effect=lambda request, view: request.role == "admin" or is_owner,
        ):
            response = api_client.delete(url)

        assert response.status_code == expected_status

        if expected_status == status.HTTP_204_NO_CONTENT:
            assert not Project.objects.filter(pk=project.id).exists()
        else:
            assert Project.objects.filter(pk=project.id).exists()


@pytest.mark.django_db
class TestProjectUser:

    @pytest.mark.parametrize(
        "is_admin, expected_status",
        [
            (True, status.HTTP_201_CREATED),
            (False, status.HTTP_403_FORBIDDEN),
        ],
    )
    def test_add_user(
        self,
        api_client,
        user_dev,
        project,
        is_admin,
        default_position,
        expected_status,
        mock_request_role,
    ):
        api_client.force_authenticate(user=user_dev)
        url = reverse("project-add-or-update-user", kwargs={"project_pk": project.id})
        data = {"user": user_dev.id, "position": default_position.id, "role": "Developer"}

        with patch.object(
            IsAdmin, "has_permission", side_effect=lambda request, view: request.role == "admin"
        ):
            response = api_client.post(url, data=data, format="json")

        resp_json = response.json()
        assert response.status_code == expected_status, resp_json

        if expected_status == status.HTTP_201_CREATED:
            assert ProjectUser.objects.count() == 1
            assert resp_json["role"] == "Developer"
        else:
            assert ProjectUser.objects.count() == 0

    @pytest.mark.parametrize(
        "role, is_admin, expected_status",
        [
            ("Developer", True, status.HTTP_200_OK),
            ("Developer", False, status.HTTP_403_FORBIDDEN),
            ("Maintainer", True, status.HTTP_200_OK),
            ("Maintainer", False, status.HTTP_200_OK),
            ("Owner", True, status.HTTP_200_OK),
            ("Owner", False, status.HTTP_200_OK),
            ("Reader", True, status.HTTP_200_OK),
            ("Reader", False, status.HTTP_403_FORBIDDEN),
        ],
    )
    def test_update_user_role(
        self,
        api_client,
        user_dev,
        project,
        default_position,
        mock_request_role,
        is_admin,
        role,
        expected_status,
        project_user,
    ):
        api_client.force_authenticate(user=user_dev)
        url = reverse("project-add-or-update-user", kwargs={"project_pk": project.id})
        data = {"user": user_dev.id, "role": "Maintainer"}

        with patch.object(
            HasProjectRole,
            "has_permission",
            side_effect=lambda request, view: request.role == "admin"
            or (role in ["Maintainer", "Owner"]),
        ):
            response = api_client.patch(url, data=data, format="json")

        resp_json = response.json()

        assert response.status_code == expected_status, resp_json

        project_user.refresh_from_db()
        if expected_status == status.HTTP_200_OK:
            assert project_user.role == "Maintainer"
        else:
            assert project_user.role == "Developer"

    @pytest.mark.parametrize(
        "role, is_admin, expected_status",
        [
            ("Developer", True, status.HTTP_204_NO_CONTENT),
            ("Developer", False, status.HTTP_403_FORBIDDEN),
            ("Maintainer", True, status.HTTP_204_NO_CONTENT),
            ("Maintainer", False, status.HTTP_403_FORBIDDEN),
            ("Owner", True, status.HTTP_204_NO_CONTENT),
            ("Owner", False, status.HTTP_204_NO_CONTENT),
            ("Reader", True, status.HTTP_204_NO_CONTENT),
            ("Reader", False, status.HTTP_403_FORBIDDEN),
        ],
    )
    def test_delete(
        self,
        api_client,
        user_dev,
        project,
        default_position,
        mock_request_role,
        is_admin,
        role,
        expected_status,
        project_user,
    ):
        api_client.force_authenticate(user=user_dev)
        url = reverse(
            "project-delete-user", kwargs={"project_pk": project.id, "user_id": user_dev.id}
        )

        with patch.object(
            HasProjectRole,
            "has_permission",
            side_effect=lambda request, view: getattr(request, "role", "user") == "admin"
            or (role in ["Owner"]),
        ):
            response = api_client.delete(url, format="json")

        resp_json = {} if response.status_code == status.HTTP_204_NO_CONTENT else response.json()

        assert response.status_code == expected_status, resp_json

        if expected_status == status.HTTP_204_NO_CONTENT:
            pass
        else:
            assert ProjectUser.objects.filter(pk=project_user.pk).exists()
