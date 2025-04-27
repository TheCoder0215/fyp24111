# certificates/services/issuance.py

from certificates.models import Certificate, DraftCertificate, Student
from certificates.services.hashing import generate_certificate_hash, sign_certificate
from blockchain.services.contract_service import add_signed_hash_to_chain
from django.conf import settings

USE_BLOCKCHAIN = settings.USE_BLOCKCHAIN

def issue_certificate_service(institution, student, certificate_type, metadata, issuing_user=None):
    """
    Issue a certificate by generating its hash, signing it, saving to DB,
    and optionally adding the signed hash to the blockchain.
    """
    # Generate the certificate hash using provided data
    certificate_hash = generate_certificate_hash(
        certificate_type=certificate_type,
        institution_id=institution.unique_identifier,
        student_id=student.unique_identifier,
        metadata=metadata
    )
    # Sign the certificate hash with institution's private key (PEM format)
    signed_hash = sign_certificate(
        certificate_hash=certificate_hash,
        private_key_pem=institution.private_key
    )
    # Create and save the Certificate instance in the database
    cert = Certificate.objects.create(
        certificate_type=certificate_type,
        certificate_hash=certificate_hash,
        signed_hash=signed_hash,
        issuing_institution=institution,
        issuing_user=issuing_user,
        student=student,
        metadata=metadata
    )

    # Determine which Ethereum credentials to use for blockchain transaction
    if issuing_user and hasattr(issuing_user, "ethereum_private_key"):
        eth_private_key = issuing_user.ethereum_private_key
        eth_address = issuing_user.ethereum_address
    else:
        eth_private_key = institution.ethereum_private_key
        eth_address = institution.ethereum_address

    # Add the signed hash to blockchain if enabled
    if USE_BLOCKCHAIN:
        try:
            add_signed_hash_to_chain(
                eth_private_key,
                eth_address,
                cert.signed_hash_keccak
            )
        except Exception as e:
            print(f"Failed to add signed hash to blockchain: {e}")

    return cert


def confirm_certificate_from_draft(draft):
    """
    Convert a DraftCertificate into a confirmed Certificate and delete the draft.
    """
    cert = issue_certificate_service(
        institution=draft.issuing_institution,
        student=draft.student,
        certificate_type=draft.certificate_type,
        metadata=draft.metadata
    )
    draft.delete()
    return cert