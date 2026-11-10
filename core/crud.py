"""Универсальные страницы управления записями: список, создание, изменение, удаление.

Кабинет модератора и панель администратора содержат много однотипных разделов
(новости, мероприятия, вакансии, справочники). Чтобы не повторять один и тот же
код, раздел описывается объектом Crud, а представления и маршруты создаются по нему.
"""
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse

from accounts.decorators import role_required

from .audit import log_action


class Crud:
    def __init__(self, *, model, form_class, name, namespace, title, title_one, columns,
                 roles, base_template, section_crumb, user_field=None, extra_actions=()):
        self.model = model
        self.form_class = form_class
        self.name = name                    # часть имени маршрута, например «news»
        self.namespace = namespace          # пространство имён приложения
        self.title = title                  # заголовок списка
        self.title_one = title_one          # название одной записи в винительном падеже
        self.columns = columns              # [(заголовок, путь к атрибуту), ...]
        self.roles = roles
        self.base_template = base_template
        self.section_crumb = section_crumb  # (название раздела, имя маршрута)
        self.user_field = user_field        # поле, куда записывается автор при создании
        self.extra_actions = extra_actions  # [(подпись, имя маршрута), ...] для строки списка

    # --- служебные методы -------------------------------------------------

    def route(self, action):
        return f"{self.namespace}:{self.name}_{action}"

    def crumbs(self, *tail):
        section_title, section_route = self.section_crumb
        items = [{"title": section_title, "url": reverse(section_route)}]
        if tail:
            items.append({"title": self.title, "url": reverse(self.route("list"))})
            items.extend({"title": title, "url": None} for title in tail)
        else:
            items.append({"title": self.title, "url": None})
        return items

    def context(self, **extra):
        return {"crud": self, "base_template": self.base_template, **extra}

    # --- представления ----------------------------------------------------

    def list_view(self, request):
        page = Paginator(self.model.objects.all(), 15).get_page(request.GET.get("page"))
        return render(request, "crud/list.html", self.context(page=page, crumbs=self.crumbs()))

    def _edit(self, request, instance, heading):
        form = self.form_class(request.POST or None, request.FILES or None, instance=instance)
        if request.method == "POST" and form.is_valid():
            obj = form.save(commit=False)
            is_new = obj.pk is None
            if is_new and self.user_field:
                setattr(obj, self.user_field, request.user)
            obj.save()
            form.save_m2m()
            log_action(request, f"{'Создание' if is_new else 'Изменение'}: {self.title_one}", obj)
            messages.success(request, "Изменения сохранены.")
            return redirect(self.route("list"))
        return render(request, "crud/form.html",
                      self.context(form=form, heading=heading, crumbs=self.crumbs(heading)))

    def create_view(self, request):
        return self._edit(request, None, f"Добавить {self.title_one}")

    def update_view(self, request, pk):
        instance = get_object_or_404(self.model, pk=pk)
        return self._edit(request, instance, f"Изменить {self.title_one}")

    def delete_view(self, request, pk):
        obj = get_object_or_404(self.model, pk=pk)
        if request.method == "POST":
            try:
                description = str(obj)
                obj.delete()
            except ProtectedError:
                messages.error(request, "Запись используется в других разделах, "
                                        "поэтому удалить её нельзя.")
            else:
                log_action(request, f"Удаление: {self.title_one}", description)
                messages.success(request, "Запись удалена.")
            return redirect(self.route("list"))
        return render(request, "crud/delete.html",
                      self.context(obj=obj, crumbs=self.crumbs("Удаление")))

    # --- маршруты ---------------------------------------------------------

    def urls(self):
        guard = role_required(*self.roles)
        return [
            path(f"{self.name}/", guard(self.list_view), name=f"{self.name}_list"),
            path(f"{self.name}/add/", guard(self.create_view), name=f"{self.name}_add"),
            path(f"{self.name}/<int:pk>/edit/", guard(self.update_view), name=f"{self.name}_edit"),
            path(f"{self.name}/<int:pk>/delete/", guard(self.delete_view),
                 name=f"{self.name}_delete"),
        ]
