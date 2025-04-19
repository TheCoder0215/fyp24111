# institutions/models.py

from django.db import models
from django.conf import settings
from institutions.services.key_management import generate_keypair, generate_unique_identifier
from django.core.exceptions import ValidationError
from web3 import Web3
import secrets

class InstitutionType(models.Model):
    INSTITUTION_TYPE_CHOICES = [
        ('education business', 'Education Business'),
        ('primary school', 'Primary School'),
        ('secondary school', 'Secondary School'),
        ('tertiary level', 'Tertiary Level'),
    ]
    CERTIFICATE_TYPE_MAPPINGS = {
        'primary school': ['certificate', 'academic_results', 'awards'],
        'secondary school': ['certificate', 'academic_results', 'awards'],
        'tertiary level': ['certificate', 'academic_results', 'awards'],
        'education business': ['certificate', 'awards'],
    }
    name = models.CharField(max_length=50, choices=INSTITUTION_TYPE_CHOICES, unique=True)
    allowed_certificate_types = models.JSONField(default=list)

    def clean(self):
        super().clean()
        if self.name:
            if self.name not in dict(self.INSTITUTION_TYPE_CHOICES):
                raise ValidationError('Invalid institution type')
            self.allowed_certificate_types = self.CERTIFICATE_TYPE_MAPPINGS[self.name]

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Institution(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='institution',
        null=True, blank=True
    )
    name = models.CharField(max_length=200, help_text="Short name or code, e.g. HKU")
    full_name = models.CharField(max_length=300, help_text="Full institution name, e.g. The University of Hong Kong")
    institution_type = models.ForeignKey(InstitutionType, on_delete=models.PROTECT)
    parent_institution = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    unique_identifier = models.CharField(max_length=64, unique=True, editable=False)
    ethereum_address = models.CharField(max_length=42, unique=True, editable=False)
    public_key = models.TextField(blank=True)
    private_key = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # concat full_name
        if self.parent_institution:
            # avoid overlapping concat
            if not self.full_name.startswith(self.parent_institution.full_name):
                self.full_name = f"{self.parent_institution.full_name} - {self.full_name or self.name}"
        if not self.name and self.user:
            self.name = self.user.username
        if not self.unique_identifier:
            parent_identifier = self.parent_institution.unique_identifier if self.parent_institution else None
            self.unique_identifier = generate_unique_identifier(self.name, parent_identifier)
        if not self.ethereum_address:
            private_key_hex = secrets.token_hex(32)
            acct = Web3().eth.account.from_key(private_key_hex)
            self.ethereum_address = acct.address
        if not self.public_key or not self.private_key:
            self.public_key, self.private_key = generate_keypair()
        super().save(*args, **kwargs)

    def regenerate_keypair(self):
        self.public_key, self.private_key = generate_keypair()
        self.save()

    def __str__(self):
        if self.parent_institution:
            return f"{self.parent_institution} / {self.name}"
        return f"{self.name}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user'], name='unique_institution_user')
        ]
        ordering = ['name']

class InstitutionUser(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, verbose_name="Belong to Institution")
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='institution_user'
    )
    full_name = models.CharField(max_length=300, blank=True, help_text="Full name of the user, e.g. C. F. Ho")
    public_key = models.TextField(blank=True)
    private_key = models.TextField(blank=True)
    unique_identifier = models.CharField(max_length=100, unique=True, editable=False)

    def save(self, *args, **kwargs):
        # concat full_name
        if self.full_name:
            if not self.full_name.startswith(self.institution.full_name):
                self.full_name = f"{self.institution.full_name} - {self.full_name}"
        else:
            self.full_name = self.institution.full_name
        if not self.unique_identifier:
            self.unique_identifier = f"{self.institution.unique_identifier}:{self.user.unique_identifier}"
        if not self.public_key or not self.private_key:
            self.public_key, self.private_key = generate_keypair()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} ({self.full_name})"

    class Meta:
        verbose_name = "Institution User"
        verbose_name_plural = "Institution Users"