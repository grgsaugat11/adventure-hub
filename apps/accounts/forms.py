from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm,
    UserCreationForm,
)

from apps.core.forms import StyledFormMixin

User = get_user_model()


class UniqueEmailMixin:
    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        users = User.objects.filter(email__iexact=email)
        if self.instance.pk:
            users = users.exclude(pk=self.instance.pk)
        if users.exists():
            raise forms.ValidationError("An account already uses this email address.")
        return email


class SignupForm(StyledFormMixin, UniqueEmailMixin, UserCreationForm):
    email = forms.EmailField(max_length=254, widget=forms.EmailInput(attrs={"autocomplete": "email"}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "username", "email", "password1", "password2")
        widgets = {
            "first_name": forms.TextInput(attrs={"autocomplete": "given-name"}),
            "last_name": forms.TextInput(attrs={"autocomplete": "family-name"}),
            "username": forms.TextInput(attrs={"autocomplete": "username"}),
        }


class ProfileForm(StyledFormMixin, UniqueEmailMixin, forms.ModelForm):
    email = forms.EmailField(max_length=254, widget=forms.EmailInput(attrs={"autocomplete": "email"}))

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        widgets = {
            "first_name": forms.TextInput(attrs={"autocomplete": "given-name"}),
            "last_name": forms.TextInput(attrs={"autocomplete": "family-name"}),
        }


class LoginForm(StyledFormMixin, AuthenticationForm):
    pass


class ChangePasswordForm(StyledFormMixin, PasswordChangeForm):
    pass


class ResetPasswordForm(StyledFormMixin, PasswordResetForm):
    pass


class NewPasswordForm(StyledFormMixin, SetPasswordForm):
    pass
