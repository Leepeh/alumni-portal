"""Операции с заявками на вступление: проверка по реестру, одобрение, отклонение."""
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import get_random_string

from accounts.models import Role, User, notify

from .models import AlumniProfile, GraduateRecord, PdConsent, RequestStatus


def find_in_registry(membership_request):
    """Ищет автора заявки в реестре выпускников, загруженном из учётной системы."""
    return GraduateRecord.objects.filter(
        last_name__iexact=membership_request.last_name,
        first_name__iexact=membership_request.first_name,
        grad_year=membership_request.grad_year,
    ).select_related("program").first()


def _set_status(membership_request, code, moderator, comment=""):
    membership_request.status = RequestStatus.objects.get(code=code)
    membership_request.reviewed_by = moderator
    membership_request.reviewed_at = timezone.now()
    membership_request.comment = comment
    membership_request.save()


@transaction.atomic
def approve_request(membership_request, moderator):
    """Одобряет заявку: создаёт учётную запись, профиль и запись о согласии.

    Все действия выполняются в одной транзакции. Возвращает пользователя
    и временный пароль, который нужно передать выпускнику.
    """
    password = get_random_string(10)
    user = User.objects.create_user(membership_request.email, password, role_code=Role.ALUMNUS)
    AlumniProfile.objects.create(
        user=user,
        program=membership_request.program,
        last_name=membership_request.last_name,
        first_name=membership_request.first_name,
        middle_name=membership_request.middle_name,
        grad_year=membership_request.grad_year,
    )
    # Согласие было дано при подаче заявки, поэтому берём дату и версию из неё
    PdConsent.objects.create(user=user, version=membership_request.consent_version,
                             given_at=membership_request.submitted_at)
    _set_status(membership_request, RequestStatus.APPROVED, moderator)
    notify(user, "Добро пожаловать в клуб выпускников! Заполните профиль и смените "
                 "временный пароль.", "/accounts/cabinet/profile/")
    send_mail(
        "Заявка на вступление в клуб выпускников одобрена",
        f"Здравствуйте, {membership_request.first_name}!\n\n"
        f"Ваша заявка одобрена. Логин: {user.email}\nВременный пароль: {password}\n"
        "После входа смените пароль в личном кабинете.",
        settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True,
    )
    return user, password


def reject_request(membership_request, moderator, comment):
    """Отклоняет заявку с указанием причины и сообщает об этом заявителю."""
    _set_status(membership_request, RequestStatus.REJECTED, moderator, comment)
    send_mail(
        "Заявка на вступление в клуб выпускников отклонена",
        f"Здравствуйте, {membership_request.first_name}!\n\n"
        f"К сожалению, заявка отклонена. Причина: {comment}",
        settings.DEFAULT_FROM_EMAIL, [membership_request.email], fail_silently=True,
    )
