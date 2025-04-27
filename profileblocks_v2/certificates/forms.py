# certificates/forms.py

from django import forms
from .models import Certificate, Student
from certificates.services.hashing import generate_student_identifier
from django.contrib.auth import get_user_model
import json
import re


class CertificateIssueForm(forms.ModelForm):
    # Field for entering the student's unique identifier
    awardee_identifier = forms.CharField(
        max_length=64,
        help_text="Enter the student's unique identifier"
    )
    
    class Meta:
        model = Certificate
        fields = ['certificate_type', 'metadata']
        widgets = {
            # Use a textarea widget for metadata input with 4 rows
            'metadata': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        # Pop institution and issuing user from kwargs for use in form logic
        self.institution = kwargs.pop('institution', None)
        self.issuing_user = kwargs.pop('issuing_user', None)
        super().__init__(*args, **kwargs)
        if self.institution:
            # Limit certificate_type choices based on institution's allowed types
            self.fields['certificate_type'].choices = [
                (ct, ct) for ct in self.institution.institution_type.allowed_certificate_types
            ]

    def clean_awardee_identifier(self):
        # Validate the awardee identifier field
        identifier = self.cleaned_data.get('awardee_identifier')
        from certificates.models import Student

        # If a Student instance is passed directly, return its unique identifier
        if isinstance(identifier, Student):
            return identifier.unique_identifier

        # Ensure the identifier is provided
        if not identifier:
            raise forms.ValidationError("This field is required.")

        # Strip whitespace and check if student with this identifier exists
        identifier = identifier.strip()
        if not Student.objects.filter(unique_identifier=identifier).exists():
            raise forms.ValidationError("Invalid student identifier")

        return identifier

    def clean(self):
        # Perform overall form validation
        cleaned_data = super().clean()

        # Ensure institution context is provided
        if not self.institution:
            raise forms.ValidationError("Institution is required")

        # Validate that metadata field contains valid JSON if it's a string
        try:
            if isinstance(cleaned_data.get('metadata'), str):
                cleaned_data['metadata'] = json.loads(cleaned_data['metadata'])
        except json.JSONDecodeError:
            raise forms.ValidationError({'metadata': 'Invalid JSON format'})

        return cleaned_data

    def save(self, commit=True):
        # Save the certificate instance with associated fields
        institution = self.institution
        issuing_user = self.issuing_user
        identifier = self.cleaned_data['awardee_identifier']

        from certificates.models import Student
        try:
            # Fetch the student by unique identifier
            student = Student.objects.get(unique_identifier=identifier)
        except Student.DoesNotExist:
            raise ValueError("Student not found")

        certificate_type = self.cleaned_data['certificate_type']
        metadata = self.cleaned_data['metadata']

        # Create a new certificate instance with the collected data
        cert = Certificate(
            issuing_institution=institution,
            issuing_user=issuing_user,
            student=student,
            certificate_type=certificate_type,
            metadata=metadata
        )

        # Save to database if commit is True
        if commit:
            cert.save()

        return cert

        
class StudentSignupForm(forms.ModelForm):
    # Fields for user login credentials
    username = forms.CharField(max_length=150, help_text="Your login username")
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = Student
        fields = ('firstname', 'lastname', 'hkid_prefix', 'date_of_birth')

    def clean(self):
        # Validate form data and enforce business rules
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        username = cleaned_data.get('username')

        # Check that both password entries match
        if password1 != password2:
            raise forms.ValidationError("Passwords do not match.")

        User = get_user_model()
        # Check for username uniqueness
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError({'username': 'This username already exists. Please choose another.'})

        hkid_prefix = cleaned_data.get('hkid_prefix')
        if hkid_prefix:
            # Validate HKID prefix format: one letter followed by exactly three digits (e.g., R123)
            if not re.match(r'^[A-Za-z]\d{3}$', hkid_prefix):
                raise forms.ValidationError({
                    'hkid_prefix': 'HKID prefix must be in the format: one letter followed by three digits (e.g., R123)'
                })

        return cleaned_data

    def save(self, commit=True):
        # Save the new student and related user account
        cleaned_data = self.cleaned_data
        User = get_user_model()
        firstname = cleaned_data['firstname']
        lastname = cleaned_data['lastname']
        hkid_prefix = cleaned_data['hkid_prefix']
        date_of_birth = cleaned_data['date_of_birth']

        # Generate a unique identifier for the student based on provided info
        unique_id = generate_student_identifier(firstname, lastname, hkid_prefix, date_of_birth)

        # Create the associated user account with student user type
        user = User.objects.create_user(
            username=cleaned_data['username'],
            password=cleaned_data['password1'],
            user_type='student',
            unique_identifier=unique_id,
        )

        # Create the Student model instance linked to the user
        student = Student(
            user=user,
            firstname=firstname,
            lastname=lastname,
            hkid_prefix=hkid_prefix,
            date_of_birth=date_of_birth,
            unique_identifier=unique_id,
        )

        # Save the student instance if commit=True
        if commit:
            student.save()

        return student