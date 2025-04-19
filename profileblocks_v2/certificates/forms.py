#certificates/forms.py
from django import forms
from .models import Certificate, Student
from certificates.services.issuance import issue_certificate
from certificates.services.hashing import generate_student_identifier
from django.contrib.auth import get_user_model
import json


class CertificateIssueForm(forms.ModelForm):

    awardee_identifier = forms.CharField(
        max_length=64,
        help_text="Enter the student's unique identifier"
    )
    
    class Meta:
        model = Certificate
        fields = ['certificate_type', 'metadata']
        widgets = {
            'metadata': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        self.institution = kwargs.pop('institution', None)
        super().__init__(*args, **kwargs)
        if self.institution:
            self.fields['certificate_type'].choices = [
                (ct, ct) for ct in self.institution.institution_type.allowed_certificate_types
            ]

    def clean_awardee_identifier(self):
        identifier = self.cleaned_data.get('awardee_identifier')
        print("DEBUG identifier type:", type(identifier))
        print(identifier)
        from certificates.models import Student
        if isinstance(identifier, Student):
            return identifier.unique_identifier
        if not identifier:
            raise forms.ValidationError("This field is required.")
        identifier = identifier.strip()
        if not Student.objects.filter(unique_identifier=identifier).exists():
            raise forms.ValidationError("Invalid student identifier")
        return identifier

    def clean(self):
        cleaned_data = super().clean()
        if not self.institution:
            raise forms.ValidationError("Institution is required")
        
        # Validate metadata is valid JSON
        try:
            if isinstance(cleaned_data.get('metadata'), str):
                cleaned_data['metadata'] = json.loads(cleaned_data['metadata'])
        except json.JSONDecodeError:
            raise forms.ValidationError({'metadata': 'Invalid JSON format'})
        
        return cleaned_data

    def save(self, commit=True):
        institution = self.institution
        identifier = self.cleaned_data['awardee_identifier']
        from certificates.models import Student
        try:
            student = Student.objects.get(unique_identifier=identifier)
        except Student.DoesNotExist:
            raise ValueError("Student not found")
        certificate_type = self.cleaned_data['certificate_type']
        metadata = self.cleaned_data['metadata']

        if commit:
            return issue_certificate(
                institution=institution,
                student=student,
                certificate_type=certificate_type,
                metadata=metadata
            )

        
class StudentSignupForm(forms.ModelForm):
    username = forms.CharField(max_length=150, help_text="Your login username")
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = Student
        fields = ('firstname', 'lastname', 'hkid_prefix', 'date_of_birth')

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        username = cleaned_data.get('username')

        if password1 != password2:
            raise forms.ValidationError("Passwords do not match.")

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError({'username': 'This username already exists. Please choose another.'})

        hkid_prefix = cleaned_data.get('hkid_prefix')
        if hkid_prefix and (not hkid_prefix.isalnum() or len(hkid_prefix) != 4):
            raise forms.ValidationError({'hkid_prefix': 'HKID prefix must be exactly 4 alphanumeric characters'})

        return cleaned_data

    def save(self, commit=True):
        cleaned_data = self.cleaned_data
        User = get_user_model()
        firstname = cleaned_data['firstname']
        lastname = cleaned_data['lastname']
        hkid_prefix = cleaned_data['hkid_prefix']
        date_of_birth = cleaned_data['date_of_birth']

        unique_id = generate_student_identifier(firstname, lastname, hkid_prefix, date_of_birth)

        user = User.objects.create_user(
            username=cleaned_data['username'],
            password=cleaned_data['password1'],
            user_type='student',
            unique_identifier=unique_id,
        )
        student = Student(
            user=user,
            firstname=firstname,
            lastname=lastname,
            hkid_prefix=hkid_prefix,
            date_of_birth=date_of_birth,
            unique_identifier=unique_id,
        )
        if commit:
            student.save()
        return student