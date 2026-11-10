from django import forms

from .models import VacancyResponse


class ResponseForm(forms.ModelForm):
    """Отклик на вакансию: резюме обязательно, письмо по желанию."""

    class Meta:
        model = VacancyResponse
        fields = ["resume_file", "cover_letter"]
        widgets = {
            "resume_file": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "cover_letter": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }
        help_texts = {
            "resume_file": "Файл PDF, DOC, DOCX, RTF или ODT размером до 5 МБ.",
        }
