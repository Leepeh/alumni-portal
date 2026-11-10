from django.db import migrations

STATUSES = [
    ("pending", "На рассмотрении"),
    ("approved", "Одобрена"),
    ("rejected", "Отклонена"),
]

# Факультет -> направления подготовки (код, название)
PROGRAMS = {
    "Факультет информационных технологий": [
        ("09.03.03", "Прикладная информатика"),
        ("38.03.05", "Бизнес-информатика"),
    ],
    "Факультет экономики и финансов": [
        ("38.03.01", "Экономика"),
        ("38.04.08", "Финансы и кредит"),
    ],
    "Факультет управления": [
        ("38.03.02", "Менеджмент"),
        ("38.03.04", "Государственное и муниципальное управление"),
    ],
    "Юридический факультет": [
        ("40.03.01", "Юриспруденция"),
    ],
}


def create_reference_data(apps, schema_editor):
    RequestStatus = apps.get_model("club", "RequestStatus")
    Faculty = apps.get_model("club", "Faculty")
    Program = apps.get_model("club", "Program")
    for code, name in STATUSES:
        RequestStatus.objects.get_or_create(code=code, defaults={"name": name})
    for faculty_name, programs in PROGRAMS.items():
        faculty, _ = Faculty.objects.get_or_create(name=faculty_name)
        for code, name in programs:
            Program.objects.get_or_create(code=code, name=name, defaults={"faculty": faculty})


def delete_reference_data(apps, schema_editor):
    apps.get_model("club", "Program").objects.all().delete()
    apps.get_model("club", "Faculty").objects.all().delete()
    apps.get_model("club", "RequestStatus").objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("club", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_reference_data, delete_reference_data),
    ]
