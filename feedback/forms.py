from django import forms

from .models import Feedback


class FeedbackForm(forms.ModelForm):
    """Форма обратной связи на странице «Контакты»."""

    consent = forms.BooleanField(
        label="Я даю согласие на обработку моих персональных данных",
        error_messages={"required": "Для отправки сообщения нужно согласие "
                                    "на обработку персональных данных."},
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = Feedback
        fields = ["name", "email", "topic", "message", "consent"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "topic": forms.TextInput(attrs={"class": "form-control"}),
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
        }

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) < 10:
            raise forms.ValidationError("Опишите вопрос подробнее (не менее 10 символов).")
        return message
