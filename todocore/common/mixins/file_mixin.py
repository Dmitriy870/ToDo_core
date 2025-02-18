from common.exception import FileDeleteError, FileUploadError
from common.files_service import (
    delete_logo_from_file_service,
    upload_logo_to_file_service,
)
from rest_framework.exceptions import ValidationError


class FileUploadMixin:
    file_field_name = None
    slugs_field_name = None

    def update_file_field(self, instance, validated_data):
        files = validated_data.get(self.file_field_name)
        if files:
            if not isinstance(files, list):
                files = [files]
            new_slugs = []
            old_slugs = getattr(instance, self.slugs_field_name, [])
            for file in files:
                try:
                    slug = upload_logo_to_file_service(file)
                except FileUploadError:
                    raise ValidationError("File upload failed")
                new_slugs.append(slug)
            for old_slug in old_slugs:
                try:
                    delete_logo_from_file_service(old_slug)
                except FileDeleteError:
                    raise ValidationError("Old file deletion failed")
            setattr(instance, self.slugs_field_name, new_slugs)
            instance.save()
        return instance
