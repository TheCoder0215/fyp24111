# blockchain/services/web3_utils.py
from web3 import Web3
from django.conf import settings

def get_web3_instance():
    # Initialize and return a Web3 instance connected to the configured HTTP provider
    return Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URL))

def get_chain_id():
    # Return the expected chain ID from Django settings
    return settings.CHAIN_ID

def check_connection():
    # Verify connection to Ethereum network and correct chain ID
    w3 = get_web3_instance()
    if not w3.is_connected():
        raise Exception("Not connected to Ethereum network")
    
    current_chain_id = w3.eth.chain_id
    if current_chain_id != settings.CHAIN_ID:
        raise Exception(f"Wrong network. Expected chain ID: {settings.CHAIN_ID}, got: {current_chain_id}")
    
    print(f"Connected: {w3.is_connected()}")
    print(f"Latest block: {w3.eth.block_number}")
    return True