# Generated by Django 5.1.4 on 2025-01-21 07:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="auth_user_id",
            field=models.UUIDField(blank=True, null=True, unique=True),
        ),
    ]
