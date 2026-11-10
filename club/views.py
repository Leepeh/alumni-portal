from django.contrib import messages
from django.shortcuts import redirect, render

from core.breadcrumbs import crumbs

from .forms import JoinForm
from .models import CONSENT_VERSION, RequestStatus


def join(request):
    """Подача заявки на вступление в клуб."""
    form = JoinForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        membership_request = form.save(commit=False)
        membership_request.status = RequestStatus.objects.get(code=RequestStatus.PENDING)
        membership_request.consent_version = CONSENT_VERSION
        membership_request.save()
        messages.success(request, "Заявка отправлена. Результат рассмотрения придёт "
                                  "на указанную электронную почту.")
        return redirect("club:join_done")
    return render(request, "club/join.html", {
        "form": form,
        "consent_version": CONSENT_VERSION,
        "crumbs": crumbs("Вступить в клуб"),
    })


def join_done(request):
    """Страница подтверждения после отправки заявки."""
    return render(request, "club/join_done.html", {
        "crumbs": crumbs(("Вступить в клуб", "club:join"), "Заявка отправлена"),
    })
