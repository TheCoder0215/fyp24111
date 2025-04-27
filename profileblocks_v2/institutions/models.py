# institutions/models.py

from django.db import models
from django.conf import settings
from institutions.services.key_management import generate_keypair, generate_unique_identifier
from django.core.exceptions import ValidationError
from eth_account import Account

class InstitutionType(models.Model):
    # Allowed institution type choices
    INSTITUTION_TYPE_CHOICES = [
        ('education business', 'Education Business'),
        ('primary school', 'Primary School'),
        ('secondary school', 'Secondary School'),
        ('tertiary level', 'Tertiary Level'),
    ]
    # Mapping from institution type to allowed certificate types
    CERTIFICATE_TYPE_MAPPINGS = {
        'primary school': ['certificate', 'academic_results', 'awards'],
        'secondary school': ['certificate', 'academic_results', 'awards'],
        'tertiary level': ['certificate', 'academic_results', 'awards'],
        'education business': ['certificate', 'awards'],
    }

    # Name of the institution type, must be unique and chosen from the defined choices
    name = models.CharField(max_length=50, choices=INSTITUTION_TYPE_CHOICES, unique=True)
    # JSON field to store list of allowed certificate types for this institution type
    allowed_certificate_types = models.JSONField(default=list)

    def clean(self):
        super().clean()
        # Validate the name is one of the allowed choices
        if self.name:
            if self.name not in dict(self.INSTITUTION_TYPE_CHOICES):
                raise ValidationError('Invalid institution type')
            # Automatically set allowed_certificate_types based on the mapping
            self.allowed_certificate_types = self.CERTIFICATE_TYPE_MAPPINGS[self.name]

    def save(self, *args, **kwargs):
        # Run full_clean to validate before saving
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Institution(models.Model):
    # One-to-one link to the Django user model, optional (null=True, blank=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='institution',
        null=True, blank=True
    )
    # Short name or code for the institution (e.g. "HKU")
    name = models.CharField(max_length=200, help_text="Short name or code, e.g. HKU")
    # Full official name (e.g. "The University of Hong Kong")
    full_name = models.CharField(max_length=300, help_text="Full institution name, e.g. The University of Hong Kong")
    # Foreign key to InstitutionType, protects on delete to avoid cascading deletes
    institution_type = models.ForeignKey(InstitutionType, on_delete=models.PROTECT)
    # Optional parent institution to form hierarchy (self-referential FK)
    parent_institution = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    # Unique identifier string, not editable by admin users
    unique_identifier = models.CharField(max_length=64, unique=True, editable=False)
    # Ethereum blockchain address (42 chars including '0x'), unique, not editable
    ethereum_address = models.CharField(max_length=42, unique=True, editable=False)
    # Ethereum private key (hex string, 0x + 64 hex digits), stored blankable for safety
    ethereum_private_key = models.CharField(max_length=66, blank=True)
    # RSA public key PEM string, optional blank
    public_key = models.TextField(blank=True)
    # RSA private key PEM string, optional blank
    private_key = models.TextField(blank=True)
    # Timestamp when institution was created, auto set on creation
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_hierarchy(self):
        """
        Return the full hierarchy chain of institution names as a string.
        Example: "The University of Hong Kong / Faculty of Engineering / Department of Computer Science"
        """
        chain = []
        current = self
        # Traverse up the parent_institution chain to build hierarchy
        while current is not None:
            chain.insert(0, current.full_name)  # Insert at beginning to build from root down
            current = current.parent_institution
        return " / ".join(chain)
    
    @property
    def hierarchy_list(self):
        # Return the hierarchy chain as a list of institution full_names
        return self.get_hierarchy().split(' / ')
    
    @property
    def root_full_name(self):
        """Return the full_name of the top-level institution in the hierarchy"""
        current = self
        # Traverse up to the root (no parent)
        while current.parent_institution is not None:
            current = current.parent_institution
        return current.full_name

    def save(self, *args, **kwargs):
        # If there is a parent institution, prepend parent's full_name to avoid overlap
        if self.parent_institution:
            # Only prepend if full_name does not already start with parent's full_name
            if not self.full_name.startswith(self.parent_institution.full_name):
                self.full_name = f"{self.parent_institution.full_name} - {self.full_name or self.name}"

        # If no short name provided but user exists, use user's username as name
        if not self.name and self.user:
            self.name = self.user.username

        # Generate unique_identifier if not already set, using parent identifier if available
        if not self.unique_identifier:
            parent_identifier = self.parent_institution.unique_identifier if self.parent_institution else None
            self.unique_identifier = generate_unique_identifier(self.name, parent_identifier)

        # Generate Ethereum keypair if missing
        if not self.ethereum_address or not self.ethereum_private_key:
            acct = Account.create()  # Generate new Ethereum account
            self.ethereum_private_key = acct.key.hex()  # Private key as hex string with 0x prefix
            self.ethereum_address = acct.address  # Ethereum address (0x...)

        # Generate RSA keypair if missing
        if not self.public_key or not self.private_key:
            self.public_key, self.private_key = generate_keypair()

        # Call parent save to persist changes
        super().save(*args, **kwargs)

    def regenerate_keypair(self):
        # Generate a new RSA public/private keypair and save
        self.public_key, self.private_key = generate_keypair()
        self.save()

    def __str__(self):
        # Display institution name with parent institution if exists
        if self.parent_institution:
            return f"{self.parent_institution} / {self.name}"
        return f"{self.name}"

    class Meta:
        # Ensure only one Institution linked to a given user
        constraints = [
            models.UniqueConstraint(fields=['user'], name='unique_institution_user')
        ]
        # Default ordering by institution name
        ordering = ['name']


class InstitutionUser(models.Model):
    # Foreign key to the institution this user belongs to
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, verbose_name="Belong to Institution")
    # One-to-one link to Django user model, with related_name for reverse lookup
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='institution_user'
    )
    # Full name of the institution user, optional but with help text
    full_name = models.CharField(max_length=300, blank=True, help_text="Full name of the user, e.g. C. F. Ho")
    # Public RSA key PEM string, optional
    public_key = models.TextField(blank=True)
    # Private RSA key PEM string, optional
    private_key = models.TextField(blank=True)
    # Unique identifier string for the institution user, uneditable and unique
    unique_identifier = models.CharField(max_length=100, unique=True, editable=False)

    @property
    def ethereum_private_key(self):
        # Delegates to the linked institution's ethereum private key
        return self.institution.ethereum_private_key

    @property
    def ethereum_address(self):
        # Delegates to the linked institution's ethereum address
        return self.institution.ethereum_address

    def save(self, *args, **kwargs):
        # If full_name provided, prepend institution's full_name if not already present
        if self.full_name:
            if not self.full_name.startswith(self.institution.full_name):
                self.full_name = f"{self.institution.full_name} - {self.full_name}"
        else:
            # If no full_name provided, default to institution's full_name
            self.full_name = self.institution.full_name

        # Generate unique_identifier using institution's unique_identifier and user's unique_identifier
        if not self.unique_identifier:
            self.unique_identifier = f"{self.institution.unique_identifier}:{self.user.unique_identifier}"

        # Generate RSA keypair if missing
        if not self.public_key or not self.private_key:
            self.public_key, self.private_key = generate_keypair()

        # Save the model instance
        super().save(*args, **kwargs)

    def __str__(self):
        # Show username and full name for display
        return f"{self.user.username} ({self.full_name})"

    class Meta:
        # Human-readable names in Django admin
        verbose_name = "Institution User"
        verbose_name_plural = "Institution Users"