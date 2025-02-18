from rest_framework import status
from rest_framework.exceptions import APIException


class InvalidOrExpiredTokenHTTPException(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED

    def __init__(self, detail: str = "Invalid or expired token"):
        super().__init__(code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class FileUploadError(Exception):
    pass


class FileDeleteError(Exception):
    pass
