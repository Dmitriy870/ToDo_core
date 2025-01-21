from uuid import uuid4

from django.db import models


class Base(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(Base):
    auth_user_id = models.UUIDField(unique=True, null=True, blank=True)

    class Meta:
        db_table = "user"


class Position(Base):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = "position"

    def __str__(self):
        return self.name
