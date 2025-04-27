# accounts/services/key_management.py
from cryptography.hazmat.primitives import serialization  # Import serialization tools for key encoding
from cryptography.hazmat.primitives.asymmetric import rsa  # Import RSA algorithm for key generation


def generate_key_pair():
    # Generate a new RSA private key with a public exponent of 65537 and 2048-bit key size
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()  # Derive the corresponding public key from the private key
    
    # Serialize the public key to PEM format (textual encoding)
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    # Serialize the private key to PEM format without encryption (PKCS8 format)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Return both keys decoded as UTF-8 strings for easy storage or transmission
    return public_pem.decode(), private_pem.decode()