import logging

import requests
from common.config import AuthConfig
from common.containers.configs import AuthConfigContainer
from common.models import User
from dependency_injector.wiring import Provide, inject
from django.db import IntegrityError
from django.http import JsonResponse
from rest_framework.status import HTTP_401_UNAUTHORIZED

logger = logging.getLogger(__name__)


def sync_user(auth_user_id):
    try:
        user, created = User.objects.get_or_create(auth_user_id=auth_user_id)
        return user
    except IntegrityError:
        return None


@inject
def token_required(get_response, config: AuthConfig = Provide[AuthConfigContainer.auth_config]):
    def middleware(request):
        if not request.path.startswith("/api/"):
            return get_response(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JsonResponse(
                {"error": "Token is missing or invalid format"},
                status=HTTP_401_UNAUTHORIZED,
            )

        token = auth_header.split(" ")[1]

        response = requests.get(
            f"{config.url}/users/me", headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code != 200:
            return JsonResponse({"error": "Invalid or expired token"}, status=HTTP_401_UNAUTHORIZED)

        user_data = response.json()
        auth_user_id = user_data.get("id")
        role = user_data.get("role")

        logger.info(f"User is {user_data}")
        user = sync_user(auth_user_id)

        request.user_id = user.id
        request.auth_user_id = auth_user_id
        request.role = role

        return get_response(request)

    return middleware
