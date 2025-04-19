# accounts/models.py

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models, transaction
from accounts.services.userid_generation import generate_user_identifier, generate_student_identifier


class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('Username must be set')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.unique_identifier = generate_user_identifier(username)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('institution', 'Institution'),
        ('student', 'Student'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, null=True)
    unique_identifier = models.CharField(max_length=64, unique=True, null=True, editable=False)

    @transaction.atomic
    def save(self, *args, **kwargs):
        if self.user_type == 'student':
            if hasattr(self, 'student'):
                s = self.student
                self.unique_identifier = generate_student_identifier(s.firstname, s.lastname, s.hkid_prefix, s.date_of_birth)
        if not self.unique_identifier:
            self.unique_identifier = generate_user_identifier(self.username)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        swappable = 'AUTH_USER_MODEL'
