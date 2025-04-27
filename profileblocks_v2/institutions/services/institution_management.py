# institutions/services/institution_management.py

from institutions.models import Institution, InstitutionUser
from institutions.services.key_management import generate_keypair, generate_unique_identifier
import secrets
from blockchain.services.contract_service import authorize_institution_on_chain
from eth_account import Account

# Generate a new Ethereum keypair using eth_account library
def generate_eth_keypair():
    acct = Account.create()  # Create a new random Ethereum account
    return acct.privateKey.hex(), acct.address

# Create a new institution record with cryptographic keys and optionally a parent institution
def create_institution(user, name, institution_type, parent_institution=None):
    # Determine parent institution's unique identifier if it exists
    parent_identifier = parent_institution.unique_identifier if parent_institution else None

    # Generate a globally unique identifier for the institution, based on name and parent
    unique_id = generate_unique_identifier(name, parent_identifier)

    # Generate public/private keypair for the institution (non-ethereum)
    public_key, private_key = generate_keypair()

    # Generate a random hex string (unused in this function but may be for other purposes)
    private_key_hex = secrets.token_hex(32)

    # Generate Ethereum keypair for blockchain interactions
    eth_private_key, ethereum_address = generate_eth_keypair()

    # Create Institution object in the database with all relevant info
    institution = Institution.objects.create(
        user=user,
        name=name,
        institution_type=institution_type,
        parent_institution=parent_institution,
        unique_identifier=unique_id,
        public_key=public_key,
        private_key=private_key,
        ethereum_private_key=eth_private_key,
        ethereum_address=ethereum_address,
    )
    
    # Attempt to authorize the institution's Ethereum address on the blockchain
    try:
        authorize_institution_on_chain(institution.ethereum_address)
    except Exception as e:
        # If blockchain authorization fails, log the error or notify admin (here just print)
        print(f"Blockchain authorization failed: {e}")
    
    return institution

# Create a new user associated with an institution, generating keys and unique ID for the user
def create_institution_user(institution, username, password):
    # Generate a public/private keypair for the institution user
    public_key, private_key = generate_keypair()

    # Construct a unique identifier for the user combining institution ID and random suffix
    unique_identifier = f"{institution.unique_identifier}:{secrets.token_hex(4)}"

    # Instantiate InstitutionUser but don't save yet
    user = InstitutionUser(
        institution=institution,
        username=username,
        public_key=public_key,
        private_key=private_key,
        unique_identifier=unique_identifier
    )
    
    # Set password securely (hashing)
    user.set_password(password)

    # Save the user to the database
    user.save()
    return user

# Regenerate the keypair for an existing institution (e.g., for key rotation)
def regenerate_institution_keypair(institution):
    # Generate new public/private keys
    public_key, private_key = generate_keypair()

    # Update institution's keys
    institution.public_key = public_key
    institution.private_key = private_key

    # Save updated keys to the database
    institution.save()
    return institution