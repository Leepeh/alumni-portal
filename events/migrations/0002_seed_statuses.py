from django.db import migrations

STATUSES = [
    ("planned", "Запланировано"),
    ("open", "Регистрация открыта"),
    ("finished", "Завершено"),
    ("cancelled", "Отменено"),
]


def create_statuses(apps, schema_editor):
    EventStatus = apps.get_model("events", "EventStatus")
    for code, name in STATUSES:
        EventStatus.objects.get_or_create(code=code, defaults={"name": name})


def delete_statuses(apps, schema_editor):
    apps.get_model("events", "EventStatus").objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_statuses, delete_statuses),
    ]
