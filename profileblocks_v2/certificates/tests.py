# certificates/tests.py
from django.test import TestCase
from blockchain.web3_utils import check_connection

class BlockchainConnectionTest(TestCase):
    def test_web3_connection(self):
        """Test if we can connect to the Sepolia testnet"""
        is_connected = check_connection()
        self.assertTrue(is_connected)