# certificates/services/issuance.py

from certificates.models import Certificate, DraftCertificate, Student
from certificates.services.hashing import generate_certificate_hash, sign_certificate
from blockchain.services.contract_service import CertificateRegistryContract

def issue_certificate(institution, student, certificate_type, metadata):
    # Generate hash & signature
    certificate_hash = generate_certificate_hash(
        certificate_type=certificate_type,
        institution_id=institution.unique_identifier,
        student_id=student.unique_identifier,
        metadata=metadata
    )
    signed_hash = sign_certificate(
        certificate_hash=certificate_hash,
        private_key_pem=institution.private_key
    )
    # Save to DB
    cert = Certificate.objects.create(
        certificate_type=certificate_type,
        certificate_hash=certificate_hash,
        signed_hash=signed_hash,
        issuing_institution=institution,
        student=student,
        metadata=metadata
    )
    # Write to blockchain
    contract = CertificateRegistryContract()
    contract.add_certificate(
        institution_id=institution.ethereum_address,
        certificate_hash=certificate_hash,
        private_key=institution.private_key
    )
    return cert

def confirm_certificate_from_draft(draft):
    cert = issue_certificate(
        institution=draft.issuing_institution,
        student=draft.student,
        certificate_type=draft.certificate_type,
        metadata=draft.metadata
    )
    draft.delete()
    return cert