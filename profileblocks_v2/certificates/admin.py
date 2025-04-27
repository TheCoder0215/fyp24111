# certificates/admin.py

from django.contrib import admin
from .models import Student, Certificate

class StudentAdmin(admin.ModelAdmin):
    # Fields to display in the list view of the admin interface for Student model
    list_display = ('get_username', 'firstname', 'lastname', 'hkid_prefix', 'date_of_birth')
    
    # Fields that will be searchable in the admin search bar
    search_fields = ('user_username', 'firstname', 'lastname', 'user_unique_identifier')
    
    def get_username(self, obj):
        """
        Custom method to display the related User's username in the list display.
        This accesses the related User object through the 'user' foreign key.
        """
        return obj.user.username

    # Set the column header name for get_username method in the admin list display
    get_username.short_description = 'Username'
    
    # Allow ordering of the list display by the related user's username field
    get_username.admin_order_field = 'user_username'


class CertificateAdmin(admin.ModelAdmin):
    # Fields to display in the list view of the admin interface for Certificate model
    list_display = ('certificate_hash', 'certificate_type', 'issuing_institution', 'student', 'created_at')
    
    # Fields to filter by in the sidebar of the admin list page
    list_filter = ('certificate_type', 'created_at', 'issuing_institution')
    
    # Fields that will be searchable in the admin search bar
    search_fields = ('certificate_hash', 'student_user_unique_identifier', 
                     'issuing_institution_user_unique_identifier')
    
    # Fields that are read-only in the admin interface (cannot be edited)
    readonly_fields = ('certificate_hash', 'created_at')


# Register the Student model with the customized StudentAdmin configuration
admin.site.register(Student, StudentAdmin)

# Register the Certificate model with the customized CertificateAdmin configuration
admin.site.register(Certificate, CertificateAdmin)