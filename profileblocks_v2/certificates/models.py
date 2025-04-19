# certificates/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from web3 import Web3
from django.utils import timezone
from certificates.services.hashing import generate_student_identifier

User = get_user_model()

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    lastname = models.CharField(max_length=100)
    firstname = models.CharField(max_length=100)
    hkid_prefix = models.CharField(max_length=4)
    date_of_birth = models.DateField()
    unique_identifier = models.CharField(max_length=64, unique=True, editable=False)


    def clean(self):
        if not self.hkid_prefix.isalnum() or len(self.hkid_prefix) != 4:
            raise ValidationError({'hkid_prefix': 'HKID prefix must be exactly 4 alphanumeric characters'})
        if not self.firstname or not self.lastname:
            raise ValidationError('Both first name and last name are required')

    def save(self, *args, **kwargs):
        new_uid = generate_student_identifier(self.firstname, self.lastname, self.hkid_prefix, self.date_of_birth)
        self.unique_identifier = new_uid
        if self.user:
            self.user.unique_identifier = new_uid
            self.user.save()
        super().save(*args, **kwargs)

    def __str__(self):
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
    
    certificate_hash = models.CharField(max_length=66, unique=True)
    certificate_type = models.CharField(max_length=20, choices=CERTIFICATE_TYPES)
    signed_hash = models.CharField(max_length=512, blank=True)
    
    issuing_institution = models.ForeignKey(
        'institutions.Institution',
        on_delete=models.PROTECT,
        related_name='issued_certificates'
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        related_name='received_certificates'
    )
    metadata = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def generate_certificate_hash(self):
        cert_info = {
            'type': self.certificate_type,
            'institution_id': self.issuing_institution.unique_identifier,
            'student_id': self.student.unique_identifier,
            'metadata': self.metadata,
            'timestamp': timezone.now().isoformat()
        }
        # Generate raw hash
        return Web3.solidity_keccak(['string'], [str(cert_info)]).hex()
    
    def sign_certificate(self):
        # Import required cryptography modules
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.backends import default_backend
        
        # Load institution's private key
        private_key = serialization.load_pem_private_key(
            self.issuing_institution.private_key.encode(),
            password=None,
            backend=default_backend()
        )
        
        # Sign the certificate hash
        signature = private_key.sign(
            self.certificate_hash.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature.hex()

    def save(self, *args, **kwargs):
        if not self.certificate_hash:
            self.certificate_hash = self.generate_certificate_hash()
        if not self.signed_hash:
            self.signed_hash = self.sign_certificate()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Certificate {self.certificate_hash[:8]} issued by {self.issuing_institution.name}"

    class Meta:
        verbose_name = "Certificate"
        verbose_name_plural = "Certificates"

class DraftCertificate(models.Model):
    certificate_type = models.CharField(max_length=20, choices=Certificate.CERTIFICATE_TYPES)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    issuing_institution = models.ForeignKey('institutions.Institution', on_delete=models.CASCADE)
    metadata = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Validate certificate type against institution type
        if not self.certificate_type in self.issuing_institution.institution_type.allowed_certificate_types:
            raise ValidationError(
                f"Institution type {self.issuing_institution.institution_type.name} "
                f"cannot issue {self.certificate_type} certificates"
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Draft Certificate"
        verbose_name_plural = "Draft Certificates"