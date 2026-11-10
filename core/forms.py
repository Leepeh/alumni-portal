from django import forms


class BootstrapMixin:
    """Добавляет полям формы классы оформления Bootstrap."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                css = "form-check-input"
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                css = "form-select"
            else:
                css = "form-control"
            widget.attrs["class"] = f"{widget.attrs.get('class', '')} {css}".strip()


class DateTimeLocalInput(forms.DateTimeInput):
    """Поле выбора даты и времени средствами браузера."""

    input_type = "datetime-local"

    def __init__(self, **kwargs):
        super().__init__(format="%Y-%m-%dT%H:%M", **kwargs)


class DateInput(forms.DateInput):
    """Поле выбора даты средствами браузера."""

    input_type = "date"

    def __init__(self, **kwargs):
        super().__init__(format="%Y-%m-%d", **kwargs)
