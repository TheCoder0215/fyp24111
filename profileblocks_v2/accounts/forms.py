# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from institutions.models import Institution
from certificates.models import Student
from .services.user_management import create_user
from django.utils import timezone
from django.forms import ValidationError
from django.db import transaction

class CustomUserCreationForm(UserCreationForm):
    institution = forms.ModelChoiceField(
        queryset=Institution.objects.all(),
        required=False,
        help_text='Select the institution this user belongs to (for institution/department users)'
    )
    firstname = forms.CharField(max_length=100, required=False)
    lastname = forms.CharField(max_length=100, required=False)
    hkid_prefix = forms.CharField(max_length=4, required=False)
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('user_type', 'institution')

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')

        if user_type == 'institution':
            if not cleaned_data.get('institution'):
                raise ValidationError({'institution': 'Institution is required for institution users'})
        elif user_type == 'student':
            required_fields = {
                'firstname': 'First name',
                'lastname': 'Last name',
                'hkid_prefix': 'HKID prefix',
                'date_of_birth': 'Date of birth'
            }
            for field, label in required_fields.items():
                if not cleaned_data.get(field):
                    raise ValidationError({field: f'{label} is required for student users'})
            hkid_prefix = cleaned_data.get('hkid_prefix')
            if hkid_prefix and (not hkid_prefix.isalnum() or len(hkid_prefix) != 4):
                raise ValidationError({'hkid_prefix': 'HKID prefix must be exactly 4 alphanumeric characters'})
            dob = cleaned_data.get('date_of_birth')
            if dob and dob > timezone.now().date():
                raise ValidationError({'date_of_birth': 'Date of birth cannot be in the future'})
        return cleaned_data

    def save(self, commit=True):
        cleaned_data = self.cleaned_data
        username = cleaned_data.get('username')
        password = cleaned_data.get('password1')
        user_type = cleaned_data.get('user_type')
        extra_fields = {}

        if user_type == 'institution':
            extra_fields['is_staff'] = True

        with transaction.atomic():
            user = create_user(username, password, user_type, **extra_fields)
            # top level institutions can be associated with a user
            # only allow assignation when parent_institution = none 
            inst = cleaned_data.get('institution')
            if user_type == 'institution' and inst and inst.parent_institution is None:
                if inst.user is None:
                    inst.user = user
                    inst.save()
                else:
                    raise ValidationError({'institution': 'This institution already has an associated user.'})
            # departmental users are managed by InstitutionUser
            
            elif user_type == 'student':
                Student.objects.create(
                    user=user,
                    firstname=cleaned_data['firstname'],
                    lastname=cleaned_data['lastname'],
                    hkid_prefix=cleaned_data['hkid_prefix'],
                    date_of_birth=cleaned_data['date_of_birth']
                )
        return user