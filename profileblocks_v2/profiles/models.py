# profiles/models.py

from django.db import models

class CertificateProfile(models.Model):
    # Use a custom char field as primary key (15 chars)
    id = models.CharField(primary_key=True, max_length=15)
    # Link profile to a Student, with cascade delete and reverse relation 'profiles'
    student = models.ForeignKey('certificates.Student', on_delete=models.CASCADE, related_name='profiles')
    # Name of the profile
    name = models.CharField(max_length=100)
    # Optional description text
    description = models.TextField(blank=True)
    # Many-to-many relation to certificates included in this profile
    certificates = models.ManyToManyField('certificates.Certificate')
    # Hash of the signed profile JSON, for verification purposes
    signed_profile_hash = models.CharField(max_length=1024)
    # Timestamp when profile was created, auto set on creation
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # String representation shows profile name and associated student
        return f"{self.name} ({self.student})"