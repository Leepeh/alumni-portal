from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm

from core.forms import BootstrapMixin

from .models import Role, User


class LoginForm(AuthenticationForm):
    """Форма входа: вместо имени пользователя используется e-mail."""

    username = forms.EmailField(
        label="Электронная почта",
        widget=forms.EmailInput(attrs={"class": "form-control", "autofocus": True}),
    )
    password = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    error_messages = {
        "invalid_login": "Неверная электронная почта или пароль.",
        "inactive": "Учётная запись отключена. Обратитесь в Центр карьеры.",
    }

    def clean_username(self):
        return self.cleaned_data["username"].lower()


class PasswordForm(BootstrapMixin, PasswordChangeForm):
    """Смена пароля с оформлением полей."""


class StaffCreateForm(BootstrapMixin, forms.Form):
    """Создание учётной записи сотрудника (модератора или администратора)."""

    email = forms.EmailField(label="Электронная почта")
    role = forms.ModelChoiceField(
        label="Роль",
        queryset=Role.objects.filter(code__in=[Role.MODERATOR, Role.ADMIN]),
        empty_label=None,
    )

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с такой почтой уже существует.")
        return email


class UserEditForm(BootstrapMixin, forms.ModelForm):
    """Изменение роли и активности учётной записи администратором."""

    class Meta:
        model = User
        fields = ["role", "is_active"]
