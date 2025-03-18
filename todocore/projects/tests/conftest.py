import pytest
from common.event import EventManager
from common.models import Position, User
from projects.api.permissions import IsProjectOwner
from projects.models import Project, ProjectUser
from rest_framework.request import Request
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_dev(db):
    return User.objects.create(auth_user_id="b4460be4-5709-4f1e-abca-de9887aca88f")


@pytest.fixture
def default_position(db):
    return Position.objects.create(name="DefaultPosition")


@pytest.fixture
def project(db, user_dev):
    return Project.objects.create(
        title="Test Project in Project",
        description="Some desc",
        status="Active",
        created_by=user_dev,
    )


@pytest.fixture
def project_user(db, project, user_dev, default_position):
    return ProjectUser.objects.create(
        project=project, user=user_dev, position=default_position, role="Developer"
    )


@pytest.fixture(autouse=True)
def disable_middleware(settings):
    settings.MIDDLEWARE = [
        m for m in settings.MIDDLEWARE if m != "common.middleware.token_required"
    ]


@pytest.fixture(autouse=True)
def patch_request_user_id():
    original_getattr = Request.__getattr__

    def patched_getattr(self, attr):
        if attr == "user_id":
            return self.user.id if self.user else None
        return original_getattr(self, attr)

    Request.__getattr__ = patched_getattr
    yield
    Request.__getattr__ = original_getattr


@pytest.fixture
def is_admin():
    return False


@pytest.fixture
def mock_request_role(monkeypatch, is_admin):
    original_init = Request.__init__

    def new_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.role = "admin" if is_admin else "user"

    monkeypatch.setattr(Request, "__init__", new_init)


@pytest.fixture
def mock_is_project_owner(monkeypatch):
    def mock_has_permission(self, request, view):
        return request.user_id == view.kwargs.get("id") or request.user_id == view.kwargs.get(
            "project_id"
        )

    monkeypatch.setattr(IsProjectOwner, "has_permission", mock_has_permission)
    monkeypatch.setattr(IsProjectOwner, "has_object_permission", mock_has_permission)


@pytest.fixture(autouse=True)
def no_kafka_events(monkeypatch):
    monkeypatch.setattr(EventManager, "send_event", lambda *args, **kwargs: None)


@pytest.fixture
def user_factory(db):
    def factory(**kwargs):
        return User.objects.create(
            auth_user_id=kwargs.get("auth_user_id", "test-user-id"),
            email=kwargs.get("email", "test@example.com"),
        )

    return factory
