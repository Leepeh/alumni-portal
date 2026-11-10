from django.contrib import messages
from django.shortcuts import redirect, render

from core.breadcrumbs import crumbs

from .forms import FeedbackForm


def contacts(request):
    """Страница «Контакты» с формой обратной связи."""
    initial = {}
    if request.user.is_authenticated:
        initial["email"] = request.user.email
        profile = getattr(request.user, "alumni_profile", None)
        if profile:
            initial["name"] = profile.first_name
    form = FeedbackForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Сообщение отправлено. Мы ответим на указанную электронную почту.")
        return redirect("feedback:contacts")
    return render(request, "feedback/contacts.html", {
        "form": form,
        "crumbs": crumbs("Контакты"),
    })
