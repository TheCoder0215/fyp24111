# certificates/services/verification.py

from blockchain.services.contract_service import verify_signed_hash_on_chain
from certificates.models import Certificate
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
import binascii

def verify_certificate_db_only(certificate_hash):
    """
    Check if the Certificate exist on DB.
    """
    try:
        cert = Certificate.objects.get(certificate_hash=certificate_hash)
        return True, cert
    except Certificate.DoesNotExist:
        return False, None
    
    
def verify_certificate_on_chain(certificate_hash):
    """
    Check if the certificate's signed hash exists on-chain.
    """
    try:
        # Get the certificate object to access its signed hash
        cert = Certificate.objects.get(certificate_hash=certificate_hash)
        signed_hash = cert.signed_hash

        # Call the blockchain contract to verify
        exists_on_chain = verify_signed_hash_on_chain(signed_hash)
        return exists_on_chain
    except Certificate.DoesNotExist:
        # Not in DB, not on chain
        return False
    except Exception as e:
        # Handle blockchain errors gracefully
        print(f"Blockchain verification error: {e}")
        return False
    

def verify_certificate_full(certificate_hash):
    """
    Stepwise verification:
      - DB existence
      - Signature validity
      - On-chain existence
    """
    try:
        cert = Certificate.objects.get(certificate_hash=certificate_hash)
    except Certificate.DoesNotExist:
        return {'db': False, 'signature': False, 'on_chain': False}

    # 1. DB check
    db_ok = True

    # 2. Signature verification
    try:
        pubkey = serialization.load_pem_public_key(cert.issuing_institution.public_key.encode())
        pubkey.verify(
            binascii.unhexlify(cert.signed_hash),
            cert.certificate_hash.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        signature_ok = True
    except Exception:
        signature_ok = False

    # 3. On-chain check (use signed_hash_keccak)
    on_chain_ok = verify_signed_hash_on_chain(cert.signed_hash_keccak)

    return {'db': db_ok, 'signature': signature_ok, 'on_chain': on_chain_ok}