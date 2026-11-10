from django import forms
from django.contrib.auth.forms import AuthenticationForm


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
