# institutions/forms.py

from django import forms
from .models import InstitutionUser, Institution

class InstitutionUserCreationForm(forms.ModelForm):
    username = forms.CharField(max_length=150, help_text="Login username for this user")
    full_name = forms.CharField(max_length=300, required=True, help_text="Full name, e.g. C. F. Ho")
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Password confirmation")

    class Meta:
        model = InstitutionUser
        fields = ('institution', 'username', 'full_name', 'password1', 'password2')

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        username = cleaned_data.get('username')

        if password1 != password2:
            raise forms.ValidationError("Passwords do not match.")

        from django.contrib.auth import get_user_model
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError({'username': 'This username already exists. Please choose another.'})

        return cleaned_data