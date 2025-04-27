# accounts/services/user_management.py
from accounts.models import User  # Import User model
from accounts.services.userid_generation import generate_user_identifier  # Import function to generate unique user ID

def create_user(username, password, user_type, **extra_fields):
    # Initialize a new User instance with username, user_type, and any additional fields
    user = User(
        username=username,
        user_type=user_type,
        **extra_fields
    )
    user.set_password(password)  # Hash and set the user's password securely
    user.unique_identifier = generate_user_identifier(username)  # Generate and assign a unique identifier based on username
    user.save()  # Save the new user instance to the database
    return user  # Return the created user object

def create_superuser(username, password, **extra_fields):
    extra_fields.setdefault('is_staff', True)  # Ensure 'is_staff' flag is True for superuser
    extra_fields.setdefault('is_superuser', True)  # Ensure 'is_superuser' flag is True for superuser
    # Create a superuser with 'institution' user_type and given credentials/fields
    return create_user(username, password, user_type='institution', **extra_fields)