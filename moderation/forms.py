from django import forms

from core.forms import BootstrapMixin, DateInput, DateTimeLocalInput
from core.models import ClubDocument, GalleryPhoto
from events.models import Event
from news.models import News
from vacancies.models import Partner, Vacancy


class NewsForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = News
        fields = ["category", "title", "summary", "body", "image", "published_at"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 10}),
            "published_at": DateTimeLocalInput(),
        }


class EventForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Event
        fields = ["title", "description", "start_at", "place", "capacity", "status"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
            "start_at": DateTimeLocalInput(),
        }

    def clean_capacity(self):
        capacity = self.cleaned_data["capacity"]
        if self.instance.pk and capacity < self.instance.registrations.count():
            raise forms.ValidationError("Количество мест не может быть меньше числа "
                                        "уже зарегистрированных участников.")
        return capacity


class PartnerForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Partner
        fields = ["name", "description", "site", "logo"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}


class VacancyForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Vacancy
        fields = ["partner", "title", "description", "salary", "is_internship", "closes_at"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 8}),
            "closes_at": DateInput(),
        }


class GalleryForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = GalleryPhoto
        fields = ["title", "image", "taken_at"]
        widgets = {"taken_at": DateInput()}


class DocumentForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = ClubDocument
        fields = ["title", "description", "file"]


class RejectForm(BootstrapMixin, forms.Form):
    """Причина отклонения заявки на вступление."""

    comment = forms.CharField(label="Причина отклонения", max_length=255,
                              widget=forms.Textarea(attrs={"rows": 3}))


class AnswerForm(BootstrapMixin, forms.Form):
    """Ответ модератора на обращение."""

    answer = forms.CharField(label="Ответ заявителю", widget=forms.Textarea(attrs={"rows": 5}))
