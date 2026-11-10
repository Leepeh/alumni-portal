import os

from django import forms
from django.utils import timezone

from club.models import Faculty, Program
from core.forms import BootstrapMixin, DateInput
from core.validators import validate_file_size


class FacultyForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Faculty
        fields = ["name"]


class ProgramForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Program
        fields = ["faculty", "code", "name"]


class ImportForm(BootstrapMixin, forms.Form):
    """Загрузка файла с реестром выпускников."""

    file = forms.FileField(label="Файл .xlsx", validators=[validate_file_size])

    def clean_file(self):
        file = self.cleaned_data["file"]
        if os.path.splitext(file.name)[1].lower() != ".xlsx":
            raise forms.ValidationError("Нужен файл формата .xlsx.")
        return file


class ReportForm(BootstrapMixin, forms.Form):
    """Период, за который формируется отчёт о деятельности клуба."""

    date_from = forms.DateField(label="Начало периода", widget=DateInput())
    date_to = forms.DateField(label="Конец периода", widget=DateInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.localdate()
        self.fields["date_from"].initial = today.replace(month=1, day=1)
        self.fields["date_to"].initial = today

    def clean(self):
        data = super().clean()
        if data.get("date_from") and data.get("date_to") and data["date_from"] > data["date_to"]:
            raise forms.ValidationError("Начало периода не может быть позже его конца.")
        return data
