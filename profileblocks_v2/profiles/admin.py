# profiles/admin.py

from django.contrib import admin
from .models import CertificateProfile

@admin.register(CertificateProfile)
class CertificateProfileAdmin(admin.ModelAdmin):
    # Fields to display in the admin list view for CertificateProfile
    list_display = ('name', 'student', 'created_at')
    # Enable search by profile name, student's username, and student's unique identifier
    search_fields = ('name', 'student__user__username', 'student__unique_identifier')
    # Add filter sidebar by creation date
    list_filter = ('created_at',)