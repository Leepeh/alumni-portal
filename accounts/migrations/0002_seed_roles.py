from django.db import migrations

ROLES = [
    ("admin", "Администратор"),
    ("moderator", "Модератор"),
    ("alumnus", "Выпускник"),
]


def create_roles(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    for code, name in ROLES:
        Role.objects.get_or_create(code=code, defaults={"name": name})


def delete_roles(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    Role.objects.filter(code__in=[code for code, _ in ROLES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_roles, delete_roles),
    ]
