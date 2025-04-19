# institutions/services/key_management.py

import secrets
import hashlib
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

def generate_keypair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    print("Generating a new keypair!")
    return public_pem.decode(), private_pem.decode()

def generate_unique_identifier(name, parent_identifier=None):
    identifier = hashlib.sha256(name.encode()).hexdigest()
    if parent_identifier:
        return f"{parent_identifier}:{identifier[0:15]}"
    return identifier[0:15]