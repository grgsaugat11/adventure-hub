from datetime import timedelta

from django import forms
from django.utils import timezone

from apps.core.forms import StyledFormMixin

from .models import BookingRequest


class BookingRequestForm(StyledFormMixin, forms.ModelForm):
    request_key = forms.CharField(widget=forms.HiddenInput)

    class Meta:
        model = BookingRequest
        fields = ("travel_date", "travellers", "contact_name", "email", "phone", "notes")
        labels = {"travel_date": "Preferred departure date", "travellers": "Number of travellers", "contact_name": "Contact name"}
        widgets = {
            "travel_date": forms.DateInput(attrs={"type": "date"}),
            "travellers": forms.NumberInput(attrs={"min": 1}),
            "contact_name": forms.TextInput(attrs={"autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "phone": forms.TextInput(attrs={"type": "tel", "autocomplete": "tel", "placeholder": "+977 …"}),
            "notes": forms.Textarea(attrs={"rows": 4, "placeholder": "Questions, preferences or anything our team should know."}),
        }
        help_texts = {"travel_date": "Our team will check availability for your preferred date.", "notes": "Optional. Please don't include passport numbers or payment details."}

    def __init__(self, *args, adventure, **kwargs):
        self.adventure = adventure
        super().__init__(*args, **kwargs)
        self.fields["travel_date"].widget.attrs["min"] = (timezone.localdate() + timedelta(days=1)).isoformat()
        self.fields["travellers"].widget.attrs["max"] = adventure.max_group_size

    def clean_travel_date(self):
        travel_date = self.cleaned_data["travel_date"]
        if travel_date <= timezone.localdate():
            raise forms.ValidationError("Choose a departure date after today.")
        return travel_date

    def clean_travellers(self):
        travellers = self.cleaned_data["travellers"]
        if travellers > self.adventure.max_group_size:
            raise forms.ValidationError(f"This adventure allows up to {self.adventure.max_group_size} travellers per request.")
        return travellers
