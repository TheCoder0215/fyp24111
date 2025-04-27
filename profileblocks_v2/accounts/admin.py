# accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .forms import CustomUserCreationForm
from certificates.models import Student
from institutions.models import Institution

# Inline admin class to display/edit related Student info within User admin
class StudentInline(admin.StackedInline):
    model = Student  # Related model to display inline
    can_delete = False  # Prevent deletion from inline
    verbose_name_plural = 'Student Information'  # Label in admin
    fields = ('lastname', 'firstname', 'hkid_prefix', 'date_of_birth')  # Fields to show/edit inline

# Inline admin class to display/edit related Institution info within User admin
class InstitutionInline(admin.StackedInline):
    model = Institution  # Related model to display inline
    can_delete = False  # Prevent deletion from inline
    verbose_name_plural = 'Institution Information'  # Label in admin
    fields = ('name', 'institution_type', 'parent_institution')  # Fields editable inline
    readonly_fields = ('unique_identifier', 'ethereum_address', 'public_key')  # Fields shown but read-only

# Custom admin class for User model extending Django's built-in UserAdmin
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm  # Custom form used when adding new users
    list_display = ('username', 'user_type', 'get_full_name', 'unique_identifier', 'is_active')  # Columns in user list view
    list_filter = ('user_type', 'is_active')  # Filters on sidebar for user_type and active status
    readonly_fields = ('unique_identifier',)  # Make unique_identifier read-only in admin detail view
    search_fields = ('username', 'unique_identifier', 'student__firstname', 'student__lastname', 'institution__name')  # Searchable fields including related models
    ordering = ('username',)  # Default ordering by username

    # Fields and layout when adding a new user via admin
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'password1', 'password2', 'user_type',
                'institution',  # Link to institution if applicable
                'firstname', 'lastname', 'hkid_prefix', 'date_of_birth'  # Personal info fields
            ),
        }),
    )

    # Custom method to show full name or institution name in list_display
    def get_full_name(self, obj):
        if hasattr(obj, 'student'):
            return f"{obj.student.firstname} {obj.student.lastname}"  # For student users, show full name
        elif hasattr(obj, 'institution'):
            return obj.institution.name  # For institution users, show institution name
        return "-"  # Default if neither related object found
    get_full_name.short_description = 'Name'  # Column header for get_full_name

    # Dynamically determine which inline admin to show based on user_type
    def get_inlines(self, request, obj=None):
        if not obj:
            return []  # No inlines when creating a new user
        if obj.user_type == 'student':
            return [StudentInline]  # Show student inline for student users
        elif obj.user_type == 'institution':
            return [InstitutionInline]  # Show institution inline for institution users
        return []  # No inlines for other user types

# Register User model with the custom admin class
admin.site.register(User, CustomUserAdmin)