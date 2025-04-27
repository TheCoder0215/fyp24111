# certificates/services/hashing.py

from web3 import Web3
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from django.utils import timezone
import hashlib

def generate_student_identifier(firstname, lastname, hkid_prefix, date_of_birth):
    """
    Generate a unique student identifier by hashing concatenated personal info.
    date_of_birth can be a datetime.date or string in 'YYYY-MM-DD' format.
    Returns first 15 hex chars of SHA-256 hash.
    """
    if hasattr(date_of_birth, 'strftime'):
        date_str = date_of_birth.strftime('%Y%m%d')
    else:
        date_str = str(date_of_birth).replace('-', '')
    data = f"{lastname}{firstname}{hkid_prefix}{date_str}"
    return hashlib.sha256(data.encode()).hexdigest()[:15]

def generate_certificate_hash(certificate_type, institution_id, student_id, metadata, timestamp=None):
    """
    Generate a solidity-compatible keccak256 hash of certificate info.
    - certificate_type: string
    - institution_id: identifier string
    - student_id: identifier string
    - metadata: any additional string metadata
    - timestamp: ISO8601 string or None (defaults to current time)
    Returns hex string with 0x prefix.
    """
    cert_info = {
        'type': certificate_type,
        'institution_id': institution_id,
        'student_id': student_id,
        'metadata': metadata,
        'timestamp': (timestamp or timezone.now().isoformat())
    }
    # Convert dict to string and hash it as solidity string type
    return Web3.solidity_keccak(['string'], [str(cert_info)]).hex()

def sign_certificate(certificate_hash, private_key_pem):
    """
    Sign the given certificate hash (hex string) using an RSA private key in PEM format.
    Returns the signature as a hex string.
    """
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode(),
        password=None,
    )
    # Sign the raw bytes of the certificate hash string (encoded as utf-8)
    signature = private_key.sign(
        certificate_hash.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature.hex()