from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from accounts.models import Role
from club import services
from club.models import AlumniProfile, Faculty, MembershipRequest, RequestStatus
from core.audit import log_action
from core.breadcrumbs import crumbs
from events.models import Event, EventRegistration
from feedback.models import Feedback
from vacancies.models import VacancyResponse

from .forms import AnswerForm, RejectForm

STAFF = (Role.MODERATOR, Role.ADMIN)
HOME = ("Кабинет модератора", "moderation:home")


@role_required(*STAFF)
def home(request):
    """Обзор: что требует внимания модератора."""
    now = timezone.now()
    return render(request, "moderation/home.html", {
        "pending_requests": MembershipRequest.objects.filter(
            status__code=RequestStatus.PENDING).count(),
        "new_feedback": Feedback.objects.filter(is_processed=False).count(),
        "upcoming_events": Event.objects.filter(start_at__gte=now).count(),
        "responses_week": VacancyResponse.objects.filter(
            created_at__gte=now - timedelta(days=7)).count(),
        "crumbs": crumbs("Кабинет модератора"),
    })


@role_required(*STAFF)
def request_list(request):
    """Заявки на вступление с фильтром по статусу."""
    status = request.GET.get("status", RequestStatus.PENDING)
    requests = MembershipRequest.objects.select_related("program", "status")
    if status != "all":
        requests = requests.filter(status__code=status)
    return render(request, "moderation/requests.html", {
        "page": Paginator(requests, 15).get_page(request.GET.get("page")),
        "status": status,
        "statuses": RequestStatus.objects.all(),
        "crumbs": crumbs(HOME, "Заявки на вступление"),
    })


@role_required(*STAFF)
def request_detail(request, pk):
    """Рассмотрение заявки: проверка по реестру, одобрение или отклонение."""
    membership_request = get_object_or_404(
        MembershipRequest.objects.select_related("program__faculty", "status"), pk=pk)
    is_pending = membership_request.status.code == RequestStatus.PENDING
    reject_form = RejectForm(request.POST or None)

    if request.method == "POST" and is_pending:
        if "approve" in request.POST:
            user, password = services.approve_request(membership_request, request.user)
            log_action(request, "Одобрение заявки на вступление", membership_request)
            messages.success(request, f"Заявка одобрена. Учётная запись {user.email} создана, "
                                      f"временный пароль: {password}")
            return redirect("moderation:requests")
        if "reject" in request.POST and reject_form.is_valid():
            services.reject_request(membership_request, request.user,
                                    reject_form.cleaned_data["comment"])
            log_action(request, "Отклонение заявки на вступление", membership_request)
            messages.info(request, "Заявка отклонена.")
            return redirect("moderation:requests")

    return render(request, "moderation/request_detail.html", {
        "item": membership_request,
        "is_pending": is_pending,
        "registry_record": services.find_in_registry(membership_request),
        "reject_form": reject_form,
        "crumbs": crumbs(HOME, ("Заявки на вступление", "moderation:requests"),
                         f"Заявка № {membership_request.pk}"),
    })


@role_required(*STAFF)
def member_list(request):
    """Реестр действующих членов клуба с поиском по фамилии, почте и факультету."""
    query = request.GET.get("q", "").strip()
    faculty_id = request.GET.get("faculty", "")
    members = AlumniProfile.objects.filter(user__is_active=True).select_related(
        "user", "program__faculty")
    if query:
        members = members.filter(Q(last_name__icontains=query) | Q(user__email__icontains=query))
    if faculty_id.isdigit():
        members = members.filter(program__faculty_id=int(faculty_id))
    return render(request, "moderation/members.html", {
        "page": Paginator(members, 20).get_page(request.GET.get("page")),
        "query": query,
        "faculty_id": int(faculty_id) if faculty_id.isdigit() else None,
        "faculties": Faculty.objects.all(),
        "crumbs": crumbs(HOME, "Члены клуба"),
    })


@role_required(*STAFF)
def feedback_list(request):
    """Обращения из формы обратной связи."""
    only_new = request.GET.get("all") != "1"
    items = Feedback.objects.all()
    if only_new:
        items = items.filter(is_processed=False)
    return render(request, "moderation/feedback.html", {
        "page": Paginator(items, 15).get_page(request.GET.get("page")),
        "only_new": only_new,
        "crumbs": crumbs(HOME, "Обращения"),
    })


@role_required(*STAFF)
def feedback_detail(request, pk):
    """Просмотр обращения и ответ на него."""
    item = get_object_or_404(Feedback, pk=pk)
    form = AnswerForm(request.POST or None, initial={"answer": item.answer})
    if request.method == "POST" and form.is_valid():
        item.answer = form.cleaned_data["answer"]
        item.is_processed = True
        item.processed_by = request.user
        item.save()
        send_mail(f"Ответ на обращение: {item.topic or 'без темы'}", item.answer,
                  settings.DEFAULT_FROM_EMAIL, [item.email], fail_silently=True)
        log_action(request, "Ответ на обращение", item)
        messages.success(request, "Ответ сохранён и отправлен заявителю.")
        return redirect("moderation:feedback")
    return render(request, "moderation/feedback_detail.html", {
        "item": item,
        "form": form,
        "crumbs": crumbs(HOME, ("Обращения", "moderation:feedback"), f"Обращение № {item.pk}"),
    })


@role_required(*STAFF)
def response_list(request):
    """Отклики выпускников на вакансии с резюме."""
    responses = VacancyResponse.objects.select_related("vacancy__partner", "profile__user")
    return render(request, "moderation/responses.html", {
        "page": Paginator(responses, 15).get_page(request.GET.get("page")),
        "crumbs": crumbs(HOME, "Отклики на вакансии"),
    })


@role_required(*STAFF)
def participants(request, pk):
    """Список участников мероприятия с отметками о посещении."""
    event = get_object_or_404(Event.objects.select_related("status"), pk=pk)
    registrations = event.registrations.select_related("profile__program", "profile__user")
    return render(request, "moderation/participants.html", {
        "event": event,
        "registrations": registrations,
        "crumbs": crumbs(HOME, ("Мероприятия", "moderation:events_list"), "Участники"),
    })


@require_POST
@role_required(*STAFF)
def toggle_attendance(request, pk):
    """Ставит или снимает отметку о посещении мероприятия."""
    registration = get_object_or_404(EventRegistration, pk=pk)
    registration.attended = not registration.attended
    registration.save(update_fields=["attended"])
    return redirect("moderation:participants", pk=registration.event_id)
