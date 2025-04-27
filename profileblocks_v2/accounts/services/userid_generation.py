import hashlib  # Import hashlib module for hashing functions

def generate_user_identifier(username):
    # Generate a unique user identifier by hashing the username
    # Encode the username to bytes, then hash using SHA-256
    # Return the first 15 characters of the hexadecimal digest
    return hashlib.sha256(username.encode()).hexdigest()[:15]

def generate_student_identifier(firstname, lastname, hkid_prefix, date_of_birth):
    # Generate a unique student identifier by hashing personal details
    
    # Check if date_of_birth has a strftime method (i.e., is a date object)
    if hasattr(date_of_birth, 'strftime'):
        # Format date_of_birth as 'YYYYMMDD'
        date_str = date_of_birth.strftime('%Y%m%d')
    else:
        # Otherwise, assume date_of_birth is a string and remove hyphens
        date_str = str(date_of_birth).replace('-', '')
    
    # Concatenate last name, first name, HKID prefix, and formatted date string
    data = f"{lastname}{firstname}{hkid_prefix}{date_str}"
    
    # Hash the concatenated string using SHA-256 and return the first 15 characters
    return hashlib.sha256(data.encode()).hexdigest()[:15]