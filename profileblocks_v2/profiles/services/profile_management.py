# profiles/services/profile_management.py

import hashlib
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

# Sign the given profile JSON string using the provided private key in PEM format
def sign_profile(profile_json, private_key_pem):
    # Load the private RSA key from PEM-encoded string (no password)
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode(),
        password=None,
    )
    # Sign the profile JSON data using RSA-PSS with SHA256 hash
    signature = private_key.sign(
        profile_json.encode(),  # Data to sign (bytes)
        padding.PSS(            # Probabilistic Signature Scheme padding
            mgf=padding.MGF1(hashes.SHA256()),  # Mask generation function with SHA256
            salt_length=padding.PSS.MAX_LENGTH  # Maximum salt length
        ),
        hashes.SHA256()         # Hash algorithm used for signing
    )
    # Hash the signature using SHA256 and take first 15 hex chars as profile ID
    digest = hashlib.sha256(signature).hexdigest()[:15]
    return digest  # Return the truncated hash as unique profile identifier