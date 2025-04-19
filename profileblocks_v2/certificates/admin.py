#certificates/admin.py
from django.contrib import admin
from .models import Student, Certificate

class StudentAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'firstname', 'lastname', 'hkid_prefix', 'date_of_birth')
    search_fields = ('user_username', 'firstname', 'lastname', 'user_unique_identifier')
    
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'
    get_username.admin_order_field = 'user_username'

class CertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_hash', 'certificate_type', 'issuing_institution', 'student', 'created_at')
    list_filter = ('certificate_type', 'created_at', 'issuing_institution')
    search_fields = ('certificate_hash', 'student_user_unique_identifier', 
                    'issuing_institution_user_unique_identifier')
    readonly_fields = ('certificate_hash', 'created_at')

admin.site.register(Student, StudentAdmin)
admin.site.register(Certificate, CertificateAdmin)