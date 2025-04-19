# certificates/services/verification.py

from blockchain.services.contract_service import CertificateRegistryContract

def verify_certificate_on_chain(certificate_hash):
    contract = CertificateRegistryContract()
    return contract.verify_certificate(certificate_hash)