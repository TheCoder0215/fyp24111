# institutions/admin.py

from django.contrib import admin
from .models import Institution, InstitutionType, InstitutionUser
from .forms import InstitutionUserCreationForm
from django.contrib.auth import get_user_model

# Register Institution model with custom admin interface
@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    # Fields to display in the list view of institutions
    list_display = (
        'name', 'full_name', 'institution_type', 'parent_institution', 'unique_identifier'
    )
    # Fields to display in the detail/edit form in the admin
    fields = (
        'name', 'full_name', 'institution_type', 'parent_institution', 'user',
        'unique_identifier', 'ethereum_address', 'ethereum_private_key',
        'public_key', 'private_key'  # Include both keys in the admin form
    )
    # Make cryptographic and identifier fields read-only for security
    readonly_fields = (
        'unique_identifier', 'ethereum_address', 'ethereum_private_key',
        'public_key', 'private_key'  # Prevent accidental edits by making read-only
    )
    # Enable search by institution name and full name in admin list view
    search_fields = ('name', 'full_name')

# Register InstitutionType model with custom admin interface
@admin.register(InstitutionType)
class InstitutionTypeAdmin(admin.ModelAdmin):
    # Display name and allowed certificate types in list view
    list_display = ('name', 'get_allowed_types')
    # Make allowed_certificate_types read-only in the admin form
    readonly_fields = ('allowed_certificate_types',)

    # Custom method to nicely display allowed certificate types as comma-separated string
    def get_allowed_types(self, obj):
        return ", ".join(obj.allowed_certificate_types or [])
    get_allowed_types.short_description = 'Allowed Certificate Types'  # Column header in admin

# Register InstitutionUser model with custom admin interface and custom form
@admin.register(InstitutionUser)
class InstitutionUserAdmin(admin.ModelAdmin):
    form = InstitutionUserCreationForm  # Use custom form for user creation/editing
    # Fields to show in the list view of institution users
    list_display = ('get_username', 'full_name', 'institution', 'unique_identifier')
    # Enable search by linked user username, full name, institution name, or unique identifier
    search_fields = ('user__username', 'full_name', 'institution__name', 'unique_identifier')
    # Make sensitive fields read-only in admin form
    readonly_fields = ('unique_identifier', 'public_key', 'private_key', 'ethereum_private_key', 'ethereum_address')
    # Organize fields into sections in admin form
    fieldsets = (
        (None, {
            'fields': ('institution', 'username', 'full_name', 'password1', 'password2')
        }),
        ('Security Information', {
            'fields': ('unique_identifier', 'public_key', 'private_key', 'ethereum_private_key', 'ethereum_address'),
            'classes': ('collapse',),  # Collapse this section by default for cleaner UI
        }),
    )

    @admin.display(description='Username')  # Label for column in admin list view
    def get_username(self, obj):
        # Return the username of linked Django user, or empty string if none
        return obj.user.username if obj.user else ""

    # Override save_model to create linked Django User when creating InstitutionUser
    def save_model(self, request, obj, form, change):
        # If this is a new InstitutionUser (not editing existing)
        if not change:
            User = get_user_model()  # Get the configured User model
            username = form.cleaned_data['username']  # Extract username from form
            password = form.cleaned_data['password1']  # Extract password from form
            # Create a new User object with institution user_type
            user = User.objects.create_user(username=username, password=password, user_type='institution')
            obj.user = user  # Link the InstitutionUser to this new User
        super().save_model(request, obj, form, change)  # Call parent to save normally