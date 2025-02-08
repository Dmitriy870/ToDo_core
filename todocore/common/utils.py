import json
from uuid import UUID

from django.db.models import Model


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)

        if isinstance(obj, Model):
            return {field.name: getattr(obj, field.name) for field in obj._meta.fields}

        return super().default(obj)
