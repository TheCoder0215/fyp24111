# blockchain/services/contract_service.py
from web3 import Web3
from django.conf import settings
import datetime
import os
import logging


def get_w3():
    # Initialize and return a Web3 instance connected to the configured HTTP provider
    return Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URL))


def get_contract():
    # Get Web3 instance and return the contract object using address and ABI from settings
    w3 = get_w3()
    return w3.eth.contract(address=settings.CONTRACT_ADDRESS, abi=settings.CONTRACT_ABI)


def authorize_institution_on_chain(institution_eth_address):
    # Authorize an institution on the blockchain contract by sending a transaction
    w3 = get_w3()
    contract = get_contract()
    nonce = w3.eth.get_transaction_count(settings.CONTRACT_OWNER_ADDRESS)  # Get nonce for transaction ordering

    # Build transaction to call authorizeInstitution function on contract
    txn = contract.functions.authorizeInstitution(institution_eth_address).build_transaction({
        'from': settings.CONTRACT_OWNER_ADDRESS,
        'nonce': nonce,
        'gas': 150000,
        'gasPrice': w3.eth.gas_price
    })

    # Sign the transaction using contract owner private key
    signed = w3.eth.account.sign_transaction(txn, settings.CONTRACT_OWNER_PRIVATE_KEY)
    # Send the signed transaction to the blockchain network
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    # Wait for transaction to be mined and get receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt


def add_signed_hash_to_chain(institution_private_key, institution_eth_address, signed_hash):
    from web3.exceptions import TransactionNotFound

    # Validate provided private key length (basic check)
    if not institution_private_key or len(institution_private_key) < 64:
        raise ValueError("Institution ETH private key is empty or invalid!")
    
    # NOTE: For proof of concept, override institution's private key and address with test account
    institution_eth_address_override = os.getenv('CONTRACT_OWNER_ADDRESS')
    institution_private_key_override = os.getenv('CONTRACT_OWNER_PRIVATE_KEY')

    # Prepare logging path as logs/cert_issues/institution_eth_address/date/signed_hash.log
    today_str = datetime.utcnow().strftime('%Y-%m-%d')
    log_dir = os.path.join(
        'logs', 'cert_issues',
        institution_eth_address_override,
        today_str
    )
    os.makedirs(log_dir, exist_ok=True)
    log_filename = os.path.join(log_dir, f"{signed_hash}.log")

    logger = logging.getLogger(f"cert_issues.{institution_eth_address_override}.{signed_hash}")
    logger.setLevel(logging.DEBUG)
    # Remove old handlers to prevent duplicate logs if function is called repeatedly
    if logger.hasHandlers():
        logger.handlers.clear()
    file_handler = logging.FileHandler(log_filename, mode='a')
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    w3 = get_w3()
    contract = get_contract()
    nonce = w3.eth.get_transaction_count(institution_eth_address_override)  # Get current nonce for the address

    logger.debug("Preparing to add signed hash to chain")
    logger.debug(f"Institution ETH Address: {institution_eth_address_override}")
    logger.debug(f"Signed hash (hex): {signed_hash}")
    logger.debug(f"Nonce: {nonce}")

    # Build transaction calling addSignedHash function with signed hash as bytes
    txn = contract.functions.addSignedHash(Web3.to_bytes(hexstr=signed_hash)).build_transaction({
        'from': institution_eth_address_override,
        'nonce': nonce,
        'gas': 150000,
        'gasPrice': w3.eth.gas_price
    })

    logger.debug(f"Transaction dict: {txn}")

    # Sign the transaction with institution's private key
    signed = w3.eth.account.sign_transaction(txn, private_key=institution_private_key_override)
    raw_tx = signed.raw_transaction
    # Send the signed transaction raw bytes to the network
    tx_hash = w3.eth.send_raw_transaction(raw_tx)
    logger.info(f"Sent transaction hash: {tx_hash.hex()}")

    try:
        logger.debug("Waiting for transaction receipt...")
        # Wait for the transaction to be mined and get receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        logger.info(f"Transaction receipt: {receipt}")
        if receipt.status == 1:
            logger.info("Transaction SUCCESSFUL")
        else:
            logger.warning("Transaction FAILED")
    except TransactionNotFound:
        logger.error("Transaction not found in mempool after sending.")
        receipt = None
    except Exception as e:
        logger.error(f"Exception while waiting for receipt: {e}")
        receipt = None

    # Clean up handler to avoid handler accumulation in repeated calls
    logger.removeHandler(file_handler)
    file_handler.close()

    return receipt


def verify_signed_hash_on_chain(signed_hash_keccak):
    # Call the contract's verifySignedHash function with the keccak hash (in bytes)
    contract = get_contract()
    return contract.functions.verifySignedHash(Web3.to_bytes(hexstr=signed_hash_keccak)).call()