import uuid

import pytest
from common.event import EventManager
from common.models import Position, User
from projects.models import Project, ProjectUser
from rest_framework.request import Request
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_dev(db):
    return User.objects.create(auth_user_id=str(uuid.uuid4()))


@pytest.fixture
def user_other(db):
    return User.objects.create(auth_user_id=str(uuid.uuid4()))


@pytest.fixture
def project(db, user_dev):
    return Project.objects.create(
        title="Test Project", description="Some desc", status="Active", created_by=user_dev
    )


@pytest.fixture
def default_position(db):
    return Position.objects.create(name="DefaultPosition")


@pytest.fixture
def add_user_to_project(db, default_position):
    def add_user(user, project, role):
        return ProjectUser.objects.create(
            project=project, user=user, position=default_position, role=role
        )

    return add_user


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


@pytest.fixture(autouse=True)
def no_kafka_events(monkeypatch):
    monkeypatch.setattr(EventManager, "send_event", lambda *args, **kwargs: None)
