from django import forms
from django.utils import timezone
from PIL import Image

from accounts.models import User
from core.forms import BootstrapMixin
from core.validators import validate_image_file

from .models import AlumniProfile, MembershipRequest, RequestStatus


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


class ProfileForm(BootstrapMixin, forms.ModelForm):
    """Редактирование профиля выпускника в личном кабинете."""

    PHOTO_SIZE = (600, 600)

    class Meta:
        model = AlumniProfile
        fields = ["last_name", "first_name", "middle_name", "program", "grad_year",
                  "workplace", "position", "is_mentor", "photo"]

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        # Проверяем только вновь загруженный файл
        if photo and hasattr(photo, "content_type"):
            validate_image_file(photo)
        return photo

    def save(self, commit=True):
        profile = super().save(commit=commit)
        if commit and "photo" in self.changed_data and profile.photo:
            # Уменьшаем фотографию, чтобы не хранить и не отдавать лишний объём
            with Image.open(profile.photo.path) as image:
                image.thumbnail(self.PHOTO_SIZE)
                image.save(profile.photo.path)
        return profile
