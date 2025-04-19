# institutions/services/institution_management.py

from institutions.models import Institution, InstitutionType, InstitutionUser
from institutions.services.key_management import generate_keypair, generate_unique_identifier
from web3 import Web3
import secrets

def create_institution(user, name, institution_type, parent_institution=None):
    parent_identifier = parent_institution.unique_identifier if parent_institution else None
    unique_id = generate_unique_identifier(name, parent_identifier)
    public_key, private_key = generate_keypair()
    private_key_hex = secrets.token_hex(32)
    ethereum_address = Web3().eth.account.from_key(private_key_hex).address

    institution = Institution.objects.create(
        user=user,
        name=name,
        institution_type=institution_type,
        parent_institution=parent_institution,
        unique_identifier=unique_id,
        public_key=public_key,
        private_key=private_key,
        ethereum_address=ethereum_address
    )
    return institution

def create_institution_user(institution, username, password):
    public_key, private_key = generate_keypair()
    unique_identifier = f"{institution.unique_identifier}:{secrets.token_hex(4)}"
    user = InstitutionUser(
        institution=institution,
        username=username,
        public_key=public_key,
        private_key=private_key,
        unique_identifier=unique_identifier
    )
    user.set_password(password)
    user.save()
    return user

def regenerate_institution_keypair(institution):
    public_key, private_key = generate_keypair()
    institution.public_key = public_key
    institution.private_key = private_key
    institution.save()
    return institution