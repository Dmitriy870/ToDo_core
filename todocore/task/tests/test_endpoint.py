from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from task.api.permissions import HasTaskRole, IsAssignee
from task.models import Task


@pytest.mark.django_db
class TestTaskViewSet:
    @pytest.mark.parametrize(
        "role, add_to_project, is_admin, expected_status",
        [
            ("Developer", True, False, status.HTTP_201_CREATED),
            ("Maintainer", True, False, status.HTTP_201_CREATED),
            ("Owner", True, False, status.HTTP_201_CREATED),
            ("Reader", True, False, status.HTTP_403_FORBIDDEN),
            ("NotInProject", False, False, status.HTTP_403_FORBIDDEN),
            ("Reader", True, True, status.HTTP_201_CREATED),
        ],
    )
    def test_create_task(
        self,
        api_client,
        user_dev,
        project,
        add_user_to_project,
        role,
        add_to_project,
        is_admin,
        expected_status,
        mock_request_role,
    ):
        if add_to_project:
            add_user_to_project(user_dev, project, role)
        api_client.force_authenticate(user=user_dev)
        url = reverse("task-list")
        data = {
            "title": "New Task",
            "description": "Some description",
            "deadline": (timezone.now() + timezone.timedelta(days=2)).isoformat(),
            "status": "New",
            "assignee": user_dev.id,
            "project": project.id,
            "created_by": user_dev.id,
        }
        with patch.object(
            HasTaskRole,
            "has_permission",
            side_effect=lambda request, view: getattr(request, "role", "user") == "admin"
            or (role in ["Developer", "Maintainer", "Owner"]),
        ):
            response = api_client.post(url, data=data, format="json")
        resp_json = response.json()
        assert response.status_code == expected_status, resp_json
        if expected_status == status.HTTP_201_CREATED:
            assert Task.objects.count() == 1
            assert resp_json["title"] == "New Task"
        else:
            assert Task.objects.count() == 0

    @pytest.mark.parametrize(
        "role, add_to_project, is_admin, expected_status",
        [
            ("Developer", True, False, status.HTTP_200_OK),
            ("Maintainer", True, False, status.HTTP_200_OK),
            ("Owner", True, False, status.HTTP_200_OK),
            ("Reader", True, False, status.HTTP_200_OK),
            ("NotInProject", False, True, status.HTTP_200_OK),
        ],
    )
    def test_retrieve_task(
        self,
        api_client,
        user_dev,
        project,
        add_user_to_project,
        role,
        add_to_project,
        is_admin,
        expected_status,
        mock_request_role,
    ):
        if add_to_project and not is_admin:
            add_user_to_project(user_dev, project, role)
        task = Task.objects.create(
            title="Task detail",
            deadline=timezone.now() + timezone.timedelta(days=1),
            status="Open",
            assignee=user_dev,
            project=project,
            created_by=user_dev,
        )
        api_client.force_authenticate(user=user_dev)
        url = reverse("task-detail", kwargs={"pk": task.pk})
        with patch.object(
            HasTaskRole,
            "has_permission",
            side_effect=lambda request, view: getattr(request, "role", "user") == "admin" or True,
        ):
            response = api_client.get(url)
        resp_json = response.json()
        assert response.status_code == expected_status, resp_json
        if expected_status == status.HTTP_200_OK:
            assert resp_json["title"] == "Task detail"

    @pytest.mark.parametrize(
        "role, add_to_project, is_assignee, is_admin, expected_status",
        [
            ("Developer", True, True, False, status.HTTP_200_OK),
            ("Developer", True, False, True, status.HTTP_200_OK),
            ("Developer", True, False, False, status.HTTP_403_FORBIDDEN),
            ("Maintainer", True, True, False, status.HTTP_200_OK),
            ("Maintainer", True, False, True, status.HTTP_200_OK),
            ("Maintainer", True, False, False, status.HTTP_403_FORBIDDEN),
            ("Owner", True, True, False, status.HTTP_200_OK),
            ("Owner", True, False, True, status.HTTP_200_OK),
            ("Owner", True, False, False, status.HTTP_403_FORBIDDEN),
            ("Reader", True, True, False, status.HTTP_403_FORBIDDEN),
            ("Reader", True, False, False, status.HTTP_403_FORBIDDEN),
            ("NotInProject", False, False, False, status.HTTP_403_FORBIDDEN),
        ],
    )
    def test_update_task(
        self,
        api_client,
        user_dev,
        user_other,
        project,
        add_user_to_project,
        role,
        add_to_project,
        is_assignee,
        is_admin,
        expected_status,
        mock_request_role,
    ):
        if add_to_project:
            add_user_to_project(user_dev, project, role)
        assignee_user = user_dev if is_assignee else user_other
        task = Task.objects.create(
            title="ToUpdate",
            deadline=timezone.now() + timezone.timedelta(days=1),
            status="Open",
            assignee=assignee_user,
            project=project,
            created_by=user_dev,
        )
        api_client.force_authenticate(user=user_dev)
        url = reverse("task-detail", kwargs={"pk": task.pk})
        add_user_to_project(user_other, project, role)
        put_data = {
            "title": "Updated Title",
            "description": "Updated desc",
            "deadline": (timezone.now() + timezone.timedelta(days=2)).isoformat(),
            "status": "InProgress",
            "project": project.id,
            "created_by": user_dev.id,
            "assignee": user_other.id,
        }
        if is_assignee:
            put_data["assignee"] = user_dev.id
        with patch.object(
            HasTaskRole,
            "has_permission",
            side_effect=lambda request, view: getattr(request, "role", "user") == "admin"
            or (role in ["Developer", "Maintainer", "Owner"]),
        ):
            with patch.object(
                IsAssignee,
                "has_permission",
                side_effect=lambda request, view: getattr(request, "role", "user") == "admin"
                or is_assignee,
            ):
                resp = api_client.put(url, data=put_data, format="json")
        resp_json = resp.json()
        assert resp.status_code == expected_status, resp_json
        if expected_status == status.HTTP_200_OK:
            assert resp_json["title"] == "Updated Title"

    @pytest.mark.parametrize(
        "role, add_to_project, is_assignee, is_admin, expected_status",
        [
            ("Developer", True, True, False, status.HTTP_200_OK),
            ("Developer", True, False, True, status.HTTP_200_OK),
            ("Developer", True, False, False, status.HTTP_403_FORBIDDEN),
            ("Maintainer", True, True, False, status.HTTP_200_OK),
            ("Maintainer", True, False, True, status.HTTP_200_OK),
            ("Maintainer", True, False, False, status.HTTP_403_FORBIDDEN),
            ("Owner", True, True, False, status.HTTP_200_OK),
            ("Owner", True, False, True, status.HTTP_200_OK),
            ("Owner", True, False, False, status.HTTP_403_FORBIDDEN),
            ("Reader", True, True, False, status.HTTP_403_FORBIDDEN),
            ("Reader", True, False, False, status.HTTP_403_FORBIDDEN),
            ("NotInProject", False, False, False, status.HTTP_403_FORBIDDEN),
        ],
    )
    def test_partial_update_task(
        self,
        api_client,
        user_dev,
        user_other,
        project,
        add_user_to_project,
        role,
        add_to_project,
        is_assignee,
        is_admin,
        expected_status,
        mock_request_role,
    ):
        if add_to_project:
            add_user_to_project(user_dev, project, role)
        assignee_user = user_dev if is_assignee else user_other
        task = Task.objects.create(
            title="PartialTask",
            deadline=timezone.now() + timezone.timedelta(days=1),
            status="Open",
            assignee=assignee_user,
            project=project,
            created_by=user_dev,
        )
        api_client.force_authenticate(user=user_dev)
        url = reverse("task-detail", kwargs={"pk": task.pk})
        patch_data = {"status": "Closed"}
        with patch.object(
            HasTaskRole,
            "has_permission",
            side_effect=lambda request, view: getattr(request, "role", "user") == "admin"
            or (role in ["Developer", "Maintainer", "Owner"]),
        ):
            with patch.object(
                IsAssignee,
                "has_permission",
                side_effect=lambda request, view: getattr(request, "role", "user") == "admin"
                or is_assignee,
            ):
                resp = api_client.patch(url, data=patch_data, format="json")
        resp_json = resp.json()
        assert resp.status_code == expected_status, resp_json
        if expected_status == status.HTTP_200_OK:
            assert resp_json["status"] == "Closed"

    @pytest.mark.parametrize(
        "role, add_to_project, is_admin, expected_status",
        [
            ("Developer", True, False, status.HTTP_403_FORBIDDEN),
            ("Maintainer", True, False, status.HTTP_403_FORBIDDEN),
            ("Owner", True, False, status.HTTP_204_NO_CONTENT),
            ("Reader", True, False, status.HTTP_403_FORBIDDEN),
            ("NotInProject", False, False, status.HTTP_403_FORBIDDEN),
            ("Developer", True, True, status.HTTP_204_NO_CONTENT),
        ],
    )
    def test_destroy_task(
        self,
        api_client,
        user_dev,
        project,
        add_user_to_project,
        role,
        add_to_project,
        is_admin,
        expected_status,
        mock_request_role,
    ):
        if add_to_project:
            add_user_to_project(user_dev, project, role)
        task = Task.objects.create(
            title="ToDelete",
            deadline=timezone.now() + timezone.timedelta(days=1),
            status="Open",
            assignee=user_dev,
            project=project,
            created_by=user_dev,
        )
        api_client.force_authenticate(user=user_dev)
        url = reverse("task-detail", kwargs={"pk": task.pk})
        with patch.object(
            HasTaskRole,
            "has_permission",
            side_effect=lambda request, view: getattr(request, "role", "user") == "admin"
            or (role == "Owner"),
        ):
            resp = api_client.delete(url)
        resp_json = {} if resp.status_code == status.HTTP_204_NO_CONTENT else resp.json()
        assert resp.status_code == expected_status, resp_json
        if expected_status == status.HTTP_204_NO_CONTENT:
            assert not Task.objects.filter(pk=task.pk).exists()
        else:
            assert Task.objects.filter(pk=task.pk).exists()

    @pytest.mark.parametrize(
        "role, add_to_project, is_admin, expected_status, expected_count",
        [
            ("Developer", True, False, status.HTTP_200_OK, 1),
            ("Maintainer", True, False, status.HTTP_200_OK, 1),
            ("Owner", True, False, status.HTTP_200_OK, 1),
            ("Reader", True, False, status.HTTP_200_OK, 1),
            ("NotInProject", False, False, status.HTTP_200_OK, 0),
            ("Developer", True, True, status.HTTP_200_OK, 1),
        ],
    )
    def test_list_tasks(
        self,
        api_client,
        user_dev,
        project,
        add_user_to_project,
        role,
        add_to_project,
        is_admin,
        expected_status,
        expected_count,
        mock_request_role,
    ):
        if add_to_project:
            add_user_to_project(user_dev, project, role)
        if expected_count == 1:
            Task.objects.create(
                title="Task for list",
                deadline=timezone.now() + timezone.timedelta(days=1),
                status="Open",
                assignee=user_dev,
                project=project,
                created_by=user_dev,
            )
        api_client.force_authenticate(user=user_dev)
        url = reverse("task-list")
        with patch.object(
            HasTaskRole,
            "has_permission",
            side_effect=lambda request, view: getattr(request, "role", "user") == "admin"
            or add_to_project,
        ):
            response = api_client.get(url)
        resp_json = response.json()
        assert response.status_code == expected_status, resp_json
        if expected_status == status.HTTP_200_OK:
            assert resp_json["count"] == expected_count
            if expected_count == 1:
                assert resp_json["results"][0]["title"] == "Task for list"

    @pytest.mark.parametrize(
        "role, add_to_project, is_admin, expected_status",
        [
            ("Developer", True, False, status.HTTP_200_OK),
            ("Developer", False, True, status.HTTP_200_OK),
            ("Maintainer", True, False, status.HTTP_200_OK),
            ("Maintainer", False, True, status.HTTP_200_OK),
            ("Owner", True, False, status.HTTP_200_OK),
            ("Owner", False, True, status.HTTP_200_OK),
            ("Reader", True, False, status.HTTP_403_FORBIDDEN),
            ("NotInProject", False, False, status.HTTP_403_FORBIDDEN),
            ("Reader", True, True, status.HTTP_200_OK),
        ],
    )
    def test_upload_files(
        self,
        api_client,
        project,
        user_dev,
        role,
        add_to_project,
        is_admin,
        expected_status,
        add_user_to_project,
        mock_request_role,
        mocker,
    ):
        mock_upload = mocker.patch(
            "common.mixins.file_mixin.upload_logo_to_file_service",
            side_effect=lambda x: f"slug-{x.name}",
        )
        mock_delete = mocker.patch(
            "common.mixins.file_mixin.delete_logo_from_file_service", return_value=True
        )

        if add_to_project:
            add_user_to_project(user_dev, project, role)

        deadline = timezone.now() + timedelta(days=7)

        task = Task.objects.create(
            title="TestTask",
            project=project,
            assignee=user_dev,
            created_by=user_dev,
            deadline=deadline,
            file_slugs=["old_slug1", "old_slug2"],
        )

        api_client.force_authenticate(user=user_dev)
        url = reverse("task-upload-files", kwargs={"pk": task.id})
        files = [
            SimpleUploadedFile("test1.txt", b"content1"),
            SimpleUploadedFile("test2.txt", b"content2"),
        ]
        data = {"files": files}
        with patch.object(HasTaskRole, "has_permission") as perm_mock:
            perm_mock.return_value = (role in ["Developer", "Maintainer", "Owner"]) or is_admin
            response = api_client.patch(url, data, format="multipart")
        assert response.status_code == expected_status, response.content.decode()

        task.refresh_from_db()
        if expected_status == status.HTTP_200_OK:
            assert mock_upload.call_count == 2
            assert set(response.data["file_slugs"]) == {"slug-test1.txt", "slug-test2.txt"}
            assert mock_delete.call_count == 2
            mock_delete.assert_has_calls(
                [mocker.call("old_slug1"), mocker.call("old_slug2")], any_order=True
            )
        else:
            mock_upload.assert_not_called()
            mock_delete.assert_not_called()
            assert task.file_slugs == ["old_slug1", "old_slug2"]
