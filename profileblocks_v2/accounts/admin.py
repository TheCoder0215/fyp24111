# accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .forms import CustomUserCreationForm
from certificates.models import Student
from institutions.models import Institution

class StudentInline(admin.StackedInline):
    model = Student
    can_delete = False
    verbose_name_plural = 'Student Information'
    fields = ('lastname', 'firstname', 'hkid_prefix', 'date_of_birth')

class InstitutionInline(admin.StackedInline):
    model = Institution
    can_delete = False
    verbose_name_plural = 'Institution Information'
    fields = ('name', 'institution_type', 'parent_institution')
    readonly_fields = ('unique_identifier', 'ethereum_address', 'public_key')

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    list_display = ('username', 'user_type', 'get_full_name', 'unique_identifier', 'is_active')
    list_filter = ('user_type', 'is_active')
    readonly_fields = ('unique_identifier',)
    search_fields = ('username', 'unique_identifier', 'student__firstname', 'student__lastname', 'institution__name')
    ordering = ('username',)

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'password1', 'password2', 'user_type',
                'institution',
                'firstname', 'lastname', 'hkid_prefix', 'date_of_birth'
            ),
        }),
    )

    def get_full_name(self, obj):
        if hasattr(obj, 'student'):
            return f"{obj.student.firstname} {obj.student.lastname}"
        elif hasattr(obj, 'institution'):
            return obj.institution.name
        return "-"
    get_full_name.short_description = 'Name'

    def get_inlines(self, request, obj=None):
        if not obj:
            return []
        if obj.user_type == 'student':
            return [StudentInline]
        elif obj.user_type == 'institution':
            return [InstitutionInline]
        return []

admin.site.register(User, CustomUserAdmin)