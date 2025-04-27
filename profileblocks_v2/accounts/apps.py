from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # Use BigAutoField as default primary key type for models
    name = 'accounts'  # Name of the Django app