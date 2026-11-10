from django import forms
from django.utils import timezone

from accounts.models import User

from .models import MembershipRequest, RequestStatus


class JoinForm(forms.ModelForm):
    """Заявка на вступление в клуб с обязательным согласием на обработку ПДн."""

    consent = forms.BooleanField(
        label="Я даю согласие на обработку моих персональных данных",
        error_messages={"required": "Без согласия на обработку персональных данных "
                                    "заявка не может быть принята."},
    )

    class Meta:
        model = MembershipRequest
        fields = ["last_name", "first_name", "middle_name", "email", "program", "grad_year"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == "consent":
                field.widget.attrs["class"] = "form-check-input"
            elif name == "program":
                field.widget.attrs["class"] = "form-select"
                field.empty_label = "Выберите направление"
            else:
                field.widget.attrs["class"] = "form-control"

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с такой почтой уже состоит в клубе. "
                                        "Войдите в личный кабинет.")
        pending = MembershipRequest.objects.filter(email=email,
                                                   status__code=RequestStatus.PENDING)
        if pending.exists():
            raise forms.ValidationError("Заявка с этой почты уже подана и ожидает рассмотрения.")
        return email

    def clean_grad_year(self):
        year = self.cleaned_data["grad_year"]
        if year > timezone.now().year:
            raise forms.ValidationError("Год выпуска не может быть позже текущего года.")
        return year
