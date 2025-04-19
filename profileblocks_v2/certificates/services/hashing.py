# certificates/services/hashing.py

from web3 import Web3
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from django.utils import timezone
import hashlib

def generate_student_identifier(firstname, lastname, hkid_prefix, date_of_birth):
    # date_of_birth: datetime.date or string 'YYYY-MM-DD'
    if hasattr(date_of_birth, 'strftime'):
        date_str = date_of_birth.strftime('%Y%m%d')
    else:
        date_str = str(date_of_birth).replace('-', '')
    data = f"{lastname}{firstname}{hkid_prefix}{date_str}"
    return hashlib.sha256(data.encode()).hexdigest()[:15]

def generate_certificate_hash(certificate_type, institution_id, student_id, metadata, timestamp=None):
    cert_info = {
        'type': certificate_type,
        'institution_id': institution_id,
        'student_id': student_id,
        'metadata': metadata,
        'timestamp': (timestamp or timezone.now().isoformat())
    }
    return Web3.solidity_keccak(['string'], [str(cert_info)]).hex()

def sign_certificate(certificate_hash, private_key_pem):
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode(),
        password=None,
    )
    signature = private_key.sign(
        certificate_hash.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature.hex()

