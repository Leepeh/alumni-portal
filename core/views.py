from django.shortcuts import render

from club.models import AlumniProfile, Faculty, MembershipRequest, Program, RequestStatus

from .breadcrumbs import crumbs


def home(request):
    """Главная страница портала со счётчиками показателей клуба."""
    stats = {
        "members": AlumniProfile.objects.count(),
        "programs": Program.objects.count(),
        "faculties": Faculty.objects.count(),
        "requests": MembershipRequest.objects.filter(
            status__code=RequestStatus.PENDING).count(),
    }
    return render(request, "core/home.html", {"stats": stats, "crumbs": []})


def about(request):
    """Страница «О клубе»: цели, направления работы, порядок вступления."""
    return render(request, "core/about.html", {"crumbs": crumbs("О клубе")})
