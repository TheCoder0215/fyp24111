# institutions/admin.py

from django.contrib import admin
from .models import Institution, InstitutionType, InstitutionUser
from .forms import InstitutionUserCreationForm
from django.contrib.auth import get_user_model

@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'full_name', 'institution_type', 'parent_institution', 'unique_identifier')
    fields = (
        'name', 'full_name', 'institution_type', 'parent_institution', 'user',
        'unique_identifier', 'ethereum_address', 'public_key'
    )
    readonly_fields = ('unique_identifier', 'ethereum_address', 'public_key')
    search_fields = ('name', 'full_name')

@admin.register(InstitutionType)
class InstitutionTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_allowed_types')
    readonly_fields = ('allowed_certificate_types',)
    def get_allowed_types(self, obj):
        return ", ".join(obj.allowed_certificate_types or [])
    get_allowed_types.short_description = 'Allowed Certificate Types'

@admin.register(InstitutionUser)
class InstitutionUserAdmin(admin.ModelAdmin):
    form = InstitutionUserCreationForm
    list_display = ('get_username', 'full_name', 'institution', 'unique_identifier')
    search_fields = ('user__username', 'full_name', 'institution__name', 'unique_identifier')
    readonly_fields = ('unique_identifier', 'public_key')
    fieldsets = (
        (None, {
            'fields': ('institution', 'username', 'full_name', 'password1', 'password2')
        }),
        ('Security Information', {
            'fields': ('unique_identifier', 'public_key'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Username')
    def get_username(self, obj):
        return obj.user.username if obj.user else ""

    def save_model(self, request, obj, form, change):
        # create User account if first time
        if not change:
            User = get_user_model()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = User.objects.create_user(username=username, password=password, user_type='institution')
            obj.user = user
        super().save_model(request, obj, form, change)