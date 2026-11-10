from django.db import migrations

CATEGORIES = [
    ("news", "Новость клуба"),
    ("story", "История выпускника"),
]


def create_categories(apps, schema_editor):
    NewsCategory = apps.get_model("news", "NewsCategory")
    for code, name in CATEGORIES:
        NewsCategory.objects.get_or_create(code=code, defaults={"name": name})


def delete_categories(apps, schema_editor):
    apps.get_model("news", "NewsCategory").objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("news", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_categories, delete_categories),
    ]
