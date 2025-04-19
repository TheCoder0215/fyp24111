import hashlib

def generate_user_identifier(username):
    return hashlib.sha256(username.encode()).hexdigest()[:15]

def generate_student_identifier(firstname, lastname, hkid_prefix, date_of_birth):
    # date_of_birth: datetime.date or string 'YYYY-MM-DD'
    if hasattr(date_of_birth, 'strftime'):
        date_str = date_of_birth.strftime('%Y%m%d')
    else:
        date_str = str(date_of_birth).replace('-', '')
    data = f"{lastname}{firstname}{hkid_prefix}{date_str}"
    return hashlib.sha256(data.encode()).hexdigest()[:15]