# accounts/services/user_management.py
from django.db import transaction
from accounts.models import User
from accounts.services.userid_generation import generate_user_identifier

def create_user(username, password, user_type, **extra_fields):
    user = User(
        username=username,
        user_type=user_type,
        **extra_fields
    )
    user.set_password(password)
    user.unique_identifier = generate_user_identifier(username)
    user.save()
    return user

def create_superuser(username, password, **extra_fields):
    extra_fields.setdefault('is_staff', True)
    extra_fields.setdefault('is_superuser', True)
    return create_user(username, password, user_type='institution', **extra_fields)