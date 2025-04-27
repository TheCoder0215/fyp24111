# institutions/forms.py

from django import forms
from .models import InstitutionUser, Institution

# Form for creating a new InstitutionUser with custom fields and validation
class InstitutionUserCreationForm(forms.ModelForm):
    # Username field for login, max length 150 chars (Django default)
    username = forms.CharField(max_length=150, help_text="Login username for this user")

    # Full name of the institution user, required field with max length 300
    full_name = forms.CharField(max_length=300, required=True, help_text="Full name, e.g. C. F. Ho")

    # Password input field, masked input
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")

    # Password confirmation input field, masked input
    password2 = forms.CharField(widget=forms.PasswordInput, label="Password confirmation")

    class Meta:
        model = InstitutionUser  # Model this form is tied to
        # Fields to include in the form
        fields = ('institution', 'username', 'full_name', 'password1', 'password2')

    # Custom validation logic for the form
    def clean(self):
        cleaned_data = super().clean()  # Run default cleaning first
        password1 = cleaned_data.get('password1')  # Get first password
        password2 = cleaned_data.get('password2')  # Get password confirmation
        username = cleaned_data.get('username')  # Get submitted username

        # Check if both password fields match
        if password1 != password2:
            raise forms.ValidationError("Passwords do not match.")  # Raise error if mismatch

        # Import User model dynamically to avoid circular imports
        from django.contrib.auth import get_user_model
        User = get_user_model()
        # Check if username is already taken in User table
        if User.objects.filter(username=username).exists():
            # Raise error attached to username field
            raise forms.ValidationError({'username': 'This username already exists. Please choose another.'})

        return cleaned_data  # Return the cleaned and validated data