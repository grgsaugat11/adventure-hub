from django import forms

from .models import ContactMessage


class StyledFormMixin:
    """Use the site's shared form controls with Django's server-side validation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.HiddenInput):
                field.widget.attrs.setdefault("class", "form-control")


class ContactForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ("name", "email", "topic", "message")
        labels = {"topic": "What can we help with?"}
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "message": forms.Textarea(attrs={"rows": 6, "placeholder": "Tell us about the adventure you're planning or include your booking reference."}),
        }
