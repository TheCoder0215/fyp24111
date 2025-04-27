# certificates/models.py

from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from web3 import Web3
from django.utils import timezone
from certificates.services.hashing import generate_student_identifier
from institutions.models import InstitutionUser
import re

User = get_user_model()  # Get the user model (custom or default)

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Link to auth user, one-to-one
    lastname = models.CharField(max_length=100)  # Student's last name
    firstname = models.CharField(max_length=100)  # Student's first name
    hkid_prefix = models.CharField(max_length=4)  # HKID prefix (expected 4 alphanumeric chars)
    date_of_birth = models.DateField()  # Student's birth date
    unique_identifier = models.CharField(max_length=64, unique=True, editable=False)  # Unique ID for student (auto-generated)
    public_key = models.TextField(blank=True, null=True)  # Student's public key for cryptographic operations
    private_key = models.TextField(blank=True, null=True)  # Student's private key (should be securely stored)

    def clean(self):
        # Validate HKID prefix format: exactly 4 alphanumeric characters
        if not re.match(r'^[A-Za-z]\d{3}$', self.hkid_prefix):
            raise ValidationError({'hkid_prefix': 'HKID prefix must be exactly 4 alphanumeric characters (eg. Y123)'})
        # Ensure both first and last names are provided
        if not self.firstname or not self.lastname:
            raise ValidationError('Both first name and last name are required')

    def save(self, *args, **kwargs):
        from accounts.services.key_management import generate_key_pair
        # Generate cryptographic key pair if not already assigned
        if not self.public_key or not self.private_key:
            pub, priv = generate_key_pair()
            self.public_key = pub
            self.private_key = priv

        # Generate unique identifier based on student info
        new_uid = generate_student_identifier(self.firstname, self.lastname, self.hkid_prefix, self.date_of_birth)
        self.unique_identifier = new_uid

        # Sync unique identifier with linked User model if user exists
        if self.user:
            self.user.unique_identifier = new_uid
            self.user.save()

        # Call the parent save method to persist the model
        super().save(*args, **kwargs)

    def __str__(self):
        # String representation: first name + last name
        return f"{self.firstname} {self.lastname}"

    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"

class Certificate(models.Model):
    CERTIFICATE_TYPES = (
        ('certificate', 'Certificate'),
        ('academic_results', 'Academic Results'),
        ('awards', 'Awards'),
    )
    
    certificate_hash = models.CharField(max_length=66, unique=True)  # Unique hash representing the certificate
    certificate_type = models.CharField(max_length=20, choices=CERTIFICATE_TYPES)  # Type of certificate
    is_public = models.BooleanField(default=False, verbose_name="Allow external access")  # Flag for external visibility
    signed_hash = models.CharField(max_length=512, blank=True)  # Signature of the certificate hash
    signed_hash_keccak = models.CharField(max_length=66, blank=True)  # Keccak hash of the signature
    
    issuing_institution = models.ForeignKey(
        'institutions.Institution',
        on_delete=models.PROTECT,  # Prevent deletion of institution if certificates exist
        related_name='issued_certificates'
    )
    issuing_user = models.ForeignKey(
        InstitutionUser,
        on_delete=models.PROTECT,  # Prevent deletion of user if certificates exist
        related_name='issued_certificates',
        null=True, blank=True,
        help_text='The actual user who issued the certificate'
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,  # Prevent deletion if student has certificates
        related_name='received_certificates'
    )
    metadata = models.JSONField()  # JSON metadata with certificate details
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of creation
    
    def generate_certificate_hash(self):
        # Prepare certificate information dictionary for hashing
        cert_info = {
            'type': self.certificate_type,
            'institution_id': self.issuing_institution.unique_identifier,
            'student_id': self.student.unique_identifier,
            'metadata': self.metadata,
            'timestamp': timezone.now().isoformat()  # Current time in ISO format to ensure uniqueness
        }
        # Generate solidity-compatible keccak hash of the stringified cert info
        return Web3.solidity_keccak(['string'], [str(cert_info)]).hex()
    
    def sign_certificate(self):
        # Import cryptography primitives for signing
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.backends import default_backend
        
        # Load the institution's private key (PEM format)
        private_key = serialization.load_pem_private_key(
            self.issuing_institution.private_key.encode(),
            password=None,
            backend=default_backend()
        )
        
        # Sign the certificate hash using PSS padding and SHA256 hashing
        signature = private_key.sign(
            self.certificate_hash.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        # Return signature in hex string format
        return signature.hex()

    def save(self, *args, **kwargs):
        # If certificate_hash is not set, generate it before saving
        if not self.certificate_hash:
            self.certificate_hash = self.generate_certificate_hash()
        # If signed hash is not set, sign the certificate hash
        if not self.signed_hash:
            self.signed_hash = self.sign_certificate()
        from web3 import Web3
        # Generate keccak hash of the signature for verification purposes
        if self.signed_hash:
            self.signed_hash_keccak = Web3.keccak(hexstr=self.signed_hash).hex()

        # Call parent save method to persist changes
        super().save(*args, **kwargs)

    def __str__(self):
        # String representation showing partial certificate hash & issuing institution
        return f"Certificate {self.certificate_hash[:8]} issued by {self.issuing_institution.name}"

    class Meta:
        verbose_name = "Certificate"
        verbose_name_plural = "Certificates"

class DraftCertificate(models.Model):
    certificate_type = models.CharField(max_length=20, choices=Certificate.CERTIFICATE_TYPES)  # Type of certificate draft
    student = models.ForeignKey(Student, on_delete=models.CASCADE)  # Reference to student for whom draft is created
    issuing_institution = models.ForeignKey('institutions.Institution', on_delete=models.CASCADE)  # Institution issuing draft
    metadata = models.JSONField()  # Draft metadata (certificate details)
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of draft creation

    def clean(self):
        # Ensure the institution type allows issuing this certificate type
        if not self.certificate_type in self.issuing_institution.institution_type.allowed_certificate_types:
            raise ValidationError(
                f"Institution type {self.issuing_institution.institution_type.name} "
                f"cannot issue {self.certificate_type} certificates"
            )

    def save(self, *args, **kwargs):
        # Validate before saving the draft
        self.full_clean()
        # Call parent save method
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Draft Certificate"
        verbose_name_plural = "Draft Certificates"