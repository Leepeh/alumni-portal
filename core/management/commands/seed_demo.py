"""Заполнение портала демонстрационными данными.

Все персональные данные вымышлены. Команда нужна для демонстрационного стенда
и для проверки портала: python manage.py seed_demo
"""
import io
import random
from datetime import timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from docx import Document
from PIL import Image, ImageDraw, ImageFont

from accounts.models import Role, User, notify
from club.models import (CONSENT_VERSION, AlumniProfile, GraduateRecord, MembershipRequest,
                         PdConsent, Program, RequestStatus)
from core.models import ClubDocument, GalleryPhoto
from events.models import Event, EventRegistration, EventStatus
from feedback.models import Feedback
from news.models import News, NewsCategory
from vacancies.models import Partner, Vacancy, VacancyResponse

# Учётные записи для проверки ролей (указываются во введении отчёта)
DEMO_ACCOUNTS = [
    ("admin@alumni-club.example", "Admin-2026-club", Role.ADMIN),
    ("moderator@alumni-club.example", "Moder-2026-club", Role.MODERATOR),
    ("alumnus@alumni-club.example", "Alumnus-2026-club", Role.ALUMNUS),
]

ALUMNI = [
    ("Соколова", "Анна", "Игоревна", "38.03.05", 2021, "ООО «Вектор Аналитика»", "Бизнес-аналитик"),
    ("Кузнецов", "Дмитрий", "Андреевич", "09.03.03", 2019, "АО «Северный поток данных»", "Разработчик"),
    ("Морозова", "Елена", "Сергеевна", "38.03.01", 2018, "ПАО «Городской кредит»", "Экономист"),
    ("Васильев", "Павел", "Олегович", "40.03.01", 2017, "Юридическое бюро «Аргумент»", "Юрист"),
    ("Новикова", "Ольга", "Викторовна", "38.03.02", 2020, "ООО «Логистик Про»", "Менеджер проектов"),
    ("Фёдоров", "Илья", "Максимович", "38.03.04", 2016, "Администрация городского округа", "Главный специалист"),
    ("Павлова", "Ксения", "Денисовна", "38.03.05", 2023, "ООО «Цифровые решения»", "Системный аналитик"),
    ("Егоров", "Артём", "Романович", "09.03.03", 2022, "ООО «Вектор Аналитика»", "Инженер данных"),
    ("Николаева", "Дарья", "Алексеевна", "38.04.08", 2024, "ПАО «Городской кредит»", "Финансовый аналитик"),
    ("Орлов", "Максим", "Евгеньевич", "40.03.01", 2015, "Коллегия адвокатов «Право и дело»", "Адвокат"),
    ("Зайцева", "Полина", "Михайловна", "38.03.02", 2021, "ООО «Экспо Медиа»", "Маркетолог"),
    ("Белов", "Никита", "Сергеевич", "38.03.01", 2019, "ООО «Логистик Про»", "Аналитик"),
]

PARTNERS = [
    ("ООО «Вектор Аналитика»", "Консалтинговая компания: бизнес-анализ и внедрение информационных систем."),
    ("АО «Северный поток данных»", "Разработчик облачных сервисов и систем хранения данных."),
    ("ПАО «Городской кредит»", "Универсальный банк, программы стажировок для молодых специалистов."),
    ("ООО «Логистик Про»", "Транспортно-логистическая компания с собственным ИТ-отделом."),
    ("Юридическое бюро «Аргумент»", "Юридическое сопровождение бизнеса и частных клиентов."),
]

VACANCIES = [
    (0, "Младший бизнес-аналитик", "от 70 000 руб.", False),
    (0, "Стажёр отдела внедрения", "оплачиваемая стажировка", True),
    (1, "Python-разработчик", "от 120 000 руб.", False),
    (1, "Инженер технической поддержки", "от 60 000 руб.", False),
    (2, "Стажёр кредитного отдела", "оплачиваемая стажировка", True),
    (2, "Финансовый аналитик", "от 90 000 руб.", False),
    (3, "Специалист по логистике", "от 65 000 руб.", False),
    (4, "Помощник юриста", "от 55 000 руб.", False),
]

NEWS = [
    ("Клуб выпускников открывает набор участников",
     "На портале начал работу приём заявок на вступление в клуб выпускников."),
    ("Итоги осеннего дня карьеры",
     "В дне карьеры приняли участие организации-партнёры и более ста студентов и выпускников."),
    ("Новые партнёры клуба",
     "К программе стажировок присоединились ещё две организации."),
    ("Запущена программа наставничества",
     "Выпускники смогут делиться опытом со студентами старших курсов."),
    ("Как подготовить резюме: советы Центра карьеры",
     "Специалисты центра рассказали, на что обращают внимание работодатели."),
    ("Встреча выпускников разных лет состоится в декабре",
     "Регистрация на встречу уже открыта в разделе «Мероприятия»."),
]

STORIES = [
    ("От стажёра до руководителя проектов",
     "Выпускница факультета управления рассказывает, как стажировка на третьем курсе помогла выбрать профессию."),
    ("Путь в бизнес-аналитику",
     "Выпускник направления «Бизнес-информатика» о первых проектах и о том, какие дисциплины пригодились в работе."),
    ("Юрист, который вернулся преподавать",
     "История выпускника юридического факультета, совмещающего практику и занятия со студентами."),
]

EVENTS = [
    (-40, "День карьеры: осень", "Главный корпус, актовый зал", 80, EventStatus.FINISHED),
    (-12, "Мастер-класс «Резюме и собеседование»", "Главный корпус, ауд. 305", 30, EventStatus.FINISHED),
    (9, "Встреча выпускников разных лет", "Главный корпус, актовый зал", 100, EventStatus.OPEN),
    (16, "Экскурсия в офис компании-партнёра", "Сбор у главного корпуса", 15, EventStatus.OPEN),
    (25, "Круглый стол «Наставничество для студентов»", "Главный корпус, ауд. 210", 25, EventStatus.OPEN),
    (45, "Зимний день карьеры", "Главный корпус, актовый зал", 80, EventStatus.PLANNED),
]

FEEDBACK = [
    ("Виктория", "viktoria@mail.example", "Вступление в клуб",
     "Здравствуйте! Я окончила университет в 2012 году, могу ли я вступить в клуб?"),
    ("Сергей", "sergey@mail.example", "Вакансии",
     "Наша организация хочет разместить вакансию для выпускников. К кому обратиться?"),
    ("Алина", "alina@mail.example", "",
     "Подскажите, пожалуйста, будет ли трансляция встречи выпускников?"),
]

COLORS = [(22, 58, 112), (200, 16, 46), (36, 84, 156), (60, 110, 90), (120, 80, 150), (200, 130, 40)]


def _font():
    """Шрифт с кириллицей: на разных системах он называется по-разному."""
    for name in ("arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"):
        try:
            return ImageFont.truetype(name, 40)
        except OSError:
            continue
    return None


def picture(text, color, size=(960, 640)):
    """Создаёт простую картинку-заглушку с подписью."""
    image = Image.new("RGB", size, color)
    draw = ImageDraw.Draw(image)
    draw.rectangle([30, 30, size[0] - 30, size[1] - 30], outline=(255, 255, 255), width=4)
    font = _font()
    if font:
        draw.text((60, size[1] // 2 - 24), text, fill=(255, 255, 255), font=font)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    return ContentFile(buffer.getvalue())


def docx_file(title, paragraphs):
    """Создаёт документ Word с заголовком и текстом."""
    document = Document()
    document.add_heading(title, level=1)
    for paragraph in paragraphs:
        document.add_paragraph(paragraph)
    buffer = io.BytesIO()
    document.save(buffer)
    return ContentFile(buffer.getvalue())


class Command(BaseCommand):
    help = "Заполняет портал вымышленными демонстрационными данными"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true",
                            help="заполнить, даже если в базе уже есть пользователи")

    @transaction.atomic
    def handle(self, *args, **options):
        if User.objects.exists() and not options["force"]:
            self.stdout.write("В базе уже есть пользователи. Для повторного заполнения "
                              "используйте ключ --force.")
            return
        random.seed(2026)
        now = timezone.now()
        programs = {program.code: program for program in Program.objects.all()}

        # --- пользователи и профили ---------------------------------------
        staff = {}
        for email, password, role in DEMO_ACCOUNTS[:2]:
            staff[role], _ = User.objects.get_or_create(email=email, defaults={
                "role": Role.objects.get(code=role)})
            staff[role].set_password(password)
            staff[role].save()
        moderator = staff[Role.MODERATOR]

        profiles = []
        for index, (last, first, middle, code, year, workplace, position) in enumerate(ALUMNI):
            if index == 0:
                email, password = DEMO_ACCOUNTS[2][0], DEMO_ACCOUNTS[2][1]
            else:
                email, password = f"alumni{index:02d}@alumni-club.example", None
            user = User.objects.create_user(email, password)
            profile = AlumniProfile.objects.create(
                user=user, program=programs[code], last_name=last, first_name=first,
                middle_name=middle, grad_year=year, workplace=workplace, position=position,
                is_mentor=index % 3 == 0)
            PdConsent.objects.create(user=user, version=CONSENT_VERSION,
                                     given_at=now - timedelta(days=60 - index))
            notify(user, "Добро пожаловать в клуб выпускников!", "/accounts/cabinet/profile/")
            profiles.append(profile)

        # --- реестр выпускников и заявки -----------------------------------
        for last, first, middle, code, year, *_ in ALUMNI:
            GraduateRecord.objects.get_or_create(last_name=last, first_name=first,
                                                 middle_name=middle, program=programs[code],
                                                 grad_year=year)
        applicants = [
            ("Григорьева", "Марина", "Павловна", "38.03.05", 2022, RequestStatus.PENDING, True),
            ("Тихонов", "Роман", "Ильич", "09.03.03", 2020, RequestStatus.PENDING, True),
            ("Лебедева", "София", "Артёмовна", "38.03.02", 2023, RequestStatus.PENDING, False),
            ("Крылов", "Глеб", "Петрович", "40.03.01", 2014, RequestStatus.REJECTED, False),
        ]
        for number, (last, first, middle, code, year, status, in_registry) in enumerate(applicants):
            if in_registry:
                GraduateRecord.objects.get_or_create(last_name=last, first_name=first,
                                                     middle_name=middle, program=programs[code],
                                                     grad_year=year)
            rejected = status == RequestStatus.REJECTED
            MembershipRequest.objects.create(
                last_name=last, first_name=first, middle_name=middle,
                email=f"applicant{number + 1}@mail.example", program=programs[code],
                grad_year=year, status=RequestStatus.objects.get(code=status),
                consent_version=CONSENT_VERSION, submitted_at=now - timedelta(days=number + 1),
                reviewed_by=moderator if rejected else None,
                reviewed_at=now if rejected else None,
                comment="Сведения об окончании университета не подтверждены." if rejected else "")

        # --- публикации ----------------------------------------------------
        categories = {category.code: category for category in NewsCategory.objects.all()}
        for index, (title, summary) in enumerate(NEWS):
            item = News(category=categories[NewsCategory.NEWS], title=title, summary=summary,
                        body=summary + "\n\nПодробности можно уточнить в Центре карьеры, практики "
                                       "и трудоустройства или через форму обратной связи на портале.",
                        published_at=now - timedelta(days=index * 6 + 1), author=moderator)
            item.image.save(f"news_{index + 1}.jpg", picture(title[:40], COLORS[index % 6]), save=False)
            item.save()
        for index, (title, summary) in enumerate(STORIES):
            News.objects.create(
                category=categories[NewsCategory.STORY], title=title, summary=summary,
                body=summary + "\n\nИстория опубликована с согласия выпускника. Имена и детали "
                               "в демонстрационной версии портала вымышлены.",
                published_at=now - timedelta(days=index * 9 + 3), author=moderator)

        # --- мероприятия и регистрации ------------------------------------
        statuses = {status.code: status for status in EventStatus.objects.all()}
        for shift, title, place, capacity, status in EVENTS:
            event = Event.objects.create(
                title=title, place=place, capacity=capacity, status=statuses[status],
                # Начало в 18:00 по местному времени
                start_at=timezone.localtime(now + timedelta(days=shift)).replace(
                    hour=18, minute=0, second=0, microsecond=0),
                description=f"{title}. Участие бесплатное, необходима регистрация на портале. "
                            "Программа мероприятия будет направлена участникам заранее.",
                created_by=moderator)
            if status == EventStatus.PLANNED:
                continue
            for profile in random.sample(profiles, k=min(len(profiles), random.randint(4, 9))):
                EventRegistration.objects.create(
                    event=event, profile=profile,
                    attended=status == EventStatus.FINISHED and random.random() < 0.8)

        # --- партнёры, вакансии, отклики ----------------------------------
        partners = [Partner.objects.create(name=name, description=description)
                    for name, description in PARTNERS]
        vacancies = []
        for index, (partner_index, title, salary, internship) in enumerate(VACANCIES):
            vacancies.append(Vacancy.objects.create(
                partner=partners[partner_index], title=title, salary=salary,
                is_internship=internship, closes_at=timezone.localdate() + timedelta(days=20 + index * 3),
                description=f"{title}. Требования: профильное образование, ответственность, "
                            "готовность учиться. Условия: оформление по ТК РФ, наставник "
                            "на период адаптации."))
        for profile, vacancy in zip(profiles[:4], vacancies[:4]):
            response = VacancyResponse(vacancy=vacancy, profile=profile,
                                       cover_letter="Добрый день! Прошу рассмотреть моё резюме.")
            response.resume_file.save(
                f"resume_{profile.pk}.docx",
                docx_file(f"Резюме: {profile.full_name}",
                          [f"Год выпуска: {profile.grad_year}", f"Место работы: {profile.workplace}",
                           "Демонстрационный документ, данные вымышлены."]), save=False)
            response.save()

        # --- обращения, галерея, документы --------------------------------
        for index, (name, email, topic, message) in enumerate(FEEDBACK):
            Feedback.objects.create(name=name, email=email, topic=topic, message=message,
                                    consent=True, is_processed=index == 0,
                                    answer="Да, вступить может выпускник любого года." if index == 0 else "",
                                    processed_by=moderator if index == 0 else None)
        for index in range(6):
            photo = GalleryPhoto(title=f"День карьеры, фото {index + 1}",
                                 taken_at=timezone.localdate() - timedelta(days=40),
                                 uploaded_by=moderator)
            photo.image.save(f"gallery_{index + 1}.jpg",
                             picture(f"Фото {index + 1}", COLORS[index]), save=False)
            photo.save()
        documents = [
            ("Положение о клубе выпускников (проект)", "Цели клуба, порядок вступления, права и обязанности членов",
             ["Проект положения подготовлен в рамках разработки портала.",
              "1. Клуб выпускников объединяет лиц, окончивших университет.",
              "2. Работу клуба организует Центр карьеры, практики и трудоустройства.",
              "3. Вступление в клуб осуществляется по заявке, поданной через портал."]),
            ("Памятка члена клуба", "Как пользоваться личным кабинетом портала",
             ["1. Заполните профиль и загрузите фотографию.",
              "2. Записывайтесь на мероприятия в разделе «Мероприятия».",
              "3. Откликайтесь на вакансии партнёров, приложив резюме."]),
        ]
        for index, (title, description, text) in enumerate(documents):
            document = ClubDocument(title=title, description=description, uploaded_by=moderator)
            document.file.save(f"document_{index + 1}.docx", docx_file(title, text), save=False)
            document.save()

        self.stdout.write(self.style.SUCCESS(
            f"Готово: пользователей {User.objects.count()}, членов клуба {len(profiles)}, "
            f"мероприятий {Event.objects.count()}, вакансий {len(vacancies)}."))
