#blockchain/services/contract_utils.py
from web3 import Web3
from django.conf import settings
from .web3_utils import get_web3_instance
from django.core.exceptions import PermissionDenied

class CertificateRegistryContract:
    def __init__(self):
        self.w3 = get_web3_instance()
        self.contract = self.w3.eth.contract(
            address=settings.CERTIFICATE_REGISTRY_ADDRESS,
            abi=settings.CERTIFICATE_REGISTRY_ABI
        )

    def add_certificate(self, institution_id, certificate_hash, private_key):
        """
        Add certificate hash to blockchain
        
        Args:
            institution_id: Institution's unique identifier
            certificate_hash: Hash of the certificate
            private_key: Institution's private key for signing
        """
        storage_string = f"{institution_id}:{certificate_hash}"
    
        function = self.contract.functions.addCertificate(
            Web3.to_bytes(text=storage_string)
        )
        
        transaction = function.build_transaction({
            'from': self.w3.to_checksum_address(institution_id),
            'nonce': self.w3.eth.get_transaction_count(institution_id),
            'gas': 100000,
            'gasPrice': self.w3.eth.gas_price
        })
        
        signed_txn = self.w3.eth.account.sign_transaction(
            transaction, 
            private_key
        )
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        return self.w3.eth.wait_for_transaction_receipt(tx_hash)

    def verify_certificate(self, certificate_hash):
        # This is a public view function, no permissions needed
        return self.contract.functions.verifyCertificate(
            Web3.to_bytes(hexstr=certificate_hash)
        ).call()

    def authorize_institution(self, admin_user, institution_address):
        # Check if user is superuser
        if not admin_user.is_superuser:
            raise PermissionDenied("Only superusers can authorize institutions")

        # Implementation depends on how you want to handle the contract owner's private key
        # You might want to store it in environment variables or a secure key management system
        owner_private_key = settings.CONTRACT_OWNER_PRIVATE_KEY

        function = self.contract.functions.authorizeInstitution(institution_address)
        
        transaction = function.build_transaction({
            'from': settings.CONTRACT_OWNER_ADDRESS,
            'nonce': self.w3.eth.get_transaction_count(settings.CONTRACT_OWNER_ADDRESS),
            'gas': 100000,
            'gasPrice': self.w3.eth.gas_price
        })

        signed_txn = self.w3.eth.account.sign_transaction(
            transaction, 
            owner_private_key
        )
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        return self.w3.eth.wait_for_transaction_receipt(tx_hash)