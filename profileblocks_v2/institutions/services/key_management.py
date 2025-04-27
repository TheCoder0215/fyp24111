# institutions/services/key_management.py

import hashlib
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# Generate an RSA public/private keypair and return PEM-encoded strings
def generate_keypair():
    # Generate a private RSA key with 2048-bit key size and public exponent 65537 (common choice)
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    # Extract the corresponding public key from the private key
    public_key = private_key.public_key()

    # Serialize the private key to PEM format with no encryption
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,  # Use PEM encoding
        format=serialization.PrivateFormat.PKCS8,  # Standard private key format
        encryption_algorithm=serialization.NoEncryption()  # No password encryption
    )

    # Serialize the public key to PEM format
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,  # PEM encoding
        format=serialization.PublicFormat.SubjectPublicKeyInfo  # Standard public key format
    )

    print("Generating a new keypair!")  # Informational print statement
    return public_pem.decode(), private_pem.decode()  # Return decoded PEM strings (text)

# Generate a unique identifier string based on a name and optional parent identifier
def generate_unique_identifier(name, parent_identifier=None):
    # Hash the provided name using SHA-256 to get a fixed-length hex digest
    identifier = hashlib.sha256(name.encode()).hexdigest()

    # If a parent identifier exists, prefix it and append first 15 chars of the hash
    if parent_identifier:
        return f"{parent_identifier}:{identifier[0:15]}"

    # Otherwise return the first 15 characters of the hash as the unique ID
    return identifier[0:15]