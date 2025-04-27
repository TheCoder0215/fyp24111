# accounts/models.py

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models, transaction
from accounts.services.userid_generation import generate_user_identifier, generate_student_identifier


class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('Username must be set')  # Ensure username is provided
        user = self.model(username=username, **extra_fields)  # Create user instance with extra fields
        user.set_password(password)  # Hash and set password
        user.unique_identifier = generate_user_identifier(username)  # Generate unique ID based on username
        user.save(using=self._db)  # Save user to the database
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)  # Ensure superuser is staff
        extra_fields.setdefault('is_superuser', True)  # Ensure superuser flag is set
        return self.create_user(username, password, **extra_fields)  # Delegate to create_user


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('institution', 'Institution'),
        ('student', 'Student'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, null=True)  # User type field
    unique_identifier = models.CharField(max_length=64, unique=True, null=True, editable=False)  # Unique ID, not editable

    @transaction.atomic
    def save(self, *args, **kwargs):
        # If user is a student and has a related student profile, generate student-specific unique identifier
        if self.user_type == 'student':
            if hasattr(self, 'student'):
                s = self.student
                self.unique_identifier = generate_student_identifier(
                    s.firstname, s.lastname, s.hkid_prefix, s.date_of_birth
                )
        # If unique_identifier not set (e.g. for institution users), generate based on username
        if not self.unique_identifier:
            self.unique_identifier = generate_user_identifier(self.username)
        super().save(*args, **kwargs)  # Call parent save method

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        swappable = 'AUTH_USER_MODEL'  # Allow swapping of this user model via settings