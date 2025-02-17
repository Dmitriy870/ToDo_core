import logging

import httpx
from common.config import CommonConfig
from common.containers.configs import CommonConfigContainer
from common.exception import FileDeleteError, FileUploadError
from dependency_injector.wiring import Provide, inject

logger = logging.getLogger(__name__)


@inject
def upload_logo_to_file_service(
    logo, common_config: CommonConfig = Provide[CommonConfigContainer.common_config]
) -> str:
    logger.info(f"Uploading file to URL: {common_config.file_service_upload_url}")
    files = {"file": (logo.name, logo.file, logo.content_type)}
    response = httpx.post(common_config.file_service_upload_url, files=files)
    if response.status_code == 200:
        data = response.json()
        slug = data.get("slug")
        if slug is None:
            logger.error("No slug returned from file service")
            raise FileUploadError("Invalid response from file service: missing 'slug'")
        return slug
    else:
        logger.error(f"File upload failed with status code: {response.status_code}")
        raise FileUploadError(f"File upload failed with status code: {response.status_code}")


@inject
def delete_logo_from_file_service(
    logo_slug: str, common_config: CommonConfig = Provide[CommonConfigContainer.common_config]
) -> None:
    delete_url = f"{common_config.file_service_delete_url}{logo_slug}"
    response = httpx.delete(delete_url)
    if response.status_code != 200:
        logger.warning(
            f"Failed to delete old logo with slug {logo_slug} (status {response.status_code})."
        )
        raise FileDeleteError(f"Failed to delete old logo with status {response.status_code}")
