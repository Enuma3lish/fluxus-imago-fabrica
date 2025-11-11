"""
ECPay Payment Gateway Client
"""
import hashlib
from urllib.parse import quote_plus, urlencode
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class ECPayClient:
    """ECPay Payment Gateway Client"""

    def __init__(self, merchant_id: str, hash_key: str, hash_iv: str, payment_url: str):
        self.merchant_id = merchant_id
        self.hash_key = hash_key
        self.hash_iv = hash_iv
        self.payment_url = payment_url

    def generate_check_mac_value(self, params: Dict[str, Any], encrypt_type: int = 1) -> str:
        """
        Generate CheckMacValue for ECPay
        Reference: https://developers.ecpay.com.tw/?p=2509

        Args:
            params: Payment parameters
            encrypt_type: 0 = MD5, 1 = SHA256 (default: 1)
        """
        # Remove CheckMacValue if exists
        params_copy = {k: v for k, v in params.items() if k != 'CheckMacValue'}

        # Convert all values to strings
        params_copy = {k: str(v) for k, v in params_copy.items()}

        # Sort parameters by key (case-sensitive alphabetical order)
        sorted_params = sorted(params_copy.items(), key=lambda x: x[0])

        # Create parameter string
        param_str = '&'.join([f'{key}={value}' for key, value in sorted_params])

        # Add HashKey and HashIV
        raw_str = f"HashKey={self.hash_key}&{param_str}&HashIV={self.hash_iv}"

        logger.debug(f"Raw string before encoding: {raw_str}")

        # URL encode
        encoded_str = quote_plus(raw_str)

        logger.debug(f"After URL encode: {encoded_str}")

        # Convert to lowercase
        encoded_str = encoded_str.lower()

        # Replace special characters back (ECPay specific requirement)
        encoded_str = encoded_str.replace('%2d', '-')
        encoded_str = encoded_str.replace('%5f', '_')
        encoded_str = encoded_str.replace('%2e', '.')
        encoded_str = encoded_str.replace('%21', '!')
        encoded_str = encoded_str.replace('%2a', '*')
        encoded_str = encoded_str.replace('%28', '(')
        encoded_str = encoded_str.replace('%29', ')')

        logger.debug(f"After special char replacement: {encoded_str}")

        # Generate hash based on encrypt_type
        if encrypt_type == 1:
            # SHA256
            check_mac_value = hashlib.sha256(encoded_str.encode('utf-8')).hexdigest().upper()
        else:
            # MD5
            check_mac_value = hashlib.md5(encoded_str.encode('utf-8')).hexdigest().upper()

        logger.info(f"Generated CheckMacValue (encrypt_type={encrypt_type}): {check_mac_value}")

        return check_mac_value

    def create_payment(
        self,
        merchant_trade_no: str,
        merchant_trade_date: str,
        total_amount: int,
        trade_desc: str,
        item_name: str,
        return_url: str,
        order_result_url: str,
        client_back_url: str,
        payment_type: str = 'aio',
        choose_payment: str = 'Credit',
        encrypt_type: int = 1
    ) -> Dict[str, Any]:
        """
        Create ECPay payment form data

        Args:
            merchant_trade_no: Order number (unique)
            merchant_trade_date: Order date (Y/m/d H:i:s)
            total_amount: Payment amount (integer)
            trade_desc: Transaction description
            item_name: Item name
            return_url: Payment callback URL
            order_result_url: Payment result URL
            client_back_url: Client return URL
            payment_type: Payment type (default: aio)
            choose_payment: Payment method (Credit/ATM/CVS/BARCODE)
            encrypt_type: Encryption type (default: 1)

        Returns:
            Dict containing payment form data
        """
        params = {
            'MerchantID': self.merchant_id,
            'MerchantTradeNo': merchant_trade_no,
            'MerchantTradeDate': merchant_trade_date,
            'PaymentType': payment_type,
            'TotalAmount': total_amount,
            'TradeDesc': trade_desc,
            'ItemName': item_name,
            'ReturnURL': return_url,
            'OrderResultURL': order_result_url,
            'ClientBackURL': client_back_url,
            'ChoosePayment': choose_payment,
            'EncryptType': encrypt_type,
        }

        # Generate CheckMacValue
        check_mac_value = self.generate_check_mac_value(params, encrypt_type)
        params['CheckMacValue'] = check_mac_value

        logger.info(f"Created payment for order: {merchant_trade_no}")

        return {
            'action_url': self.payment_url,
            'params': params
        }

    def verify_callback(self, callback_data: Dict[str, Any]) -> bool:
        """
        Verify ECPay payment callback data

        Args:
            callback_data: Callback data from ECPay

        Returns:
            True if verification succeeds, False otherwise
        """
        if 'CheckMacValue' not in callback_data:
            logger.error("CheckMacValue not found in callback data")
            return False

        # Extract CheckMacValue from callback
        received_check_mac = callback_data.pop('CheckMacValue')

        # Generate CheckMacValue from callback data
        calculated_check_mac = self.generate_check_mac_value(callback_data)

        # Compare
        is_valid = received_check_mac == calculated_check_mac

        if is_valid:
            logger.info(f"Payment callback verified for order: {callback_data.get('MerchantTradeNo')}")
        else:
            logger.error(f"Payment callback verification failed for order: {callback_data.get('MerchantTradeNo')}")

        # Restore CheckMacValue
        callback_data['CheckMacValue'] = received_check_mac

        return is_valid

    def query_payment(self, merchant_trade_no: str, query_url: str) -> Dict[str, Any]:
        """
        Query payment status from ECPay

        Args:
            merchant_trade_no: Order number
            query_url: ECPay query URL

        Returns:
            Dict containing payment status
        """
        import requests

        params = {
            'MerchantID': self.merchant_id,
            'MerchantTradeNo': merchant_trade_no,
            'TimeStamp': str(int(time.time())),
        }

        # Generate CheckMacValue
        check_mac_value = self.generate_check_mac_value(params)
        params['CheckMacValue'] = check_mac_value

        try:
            response = requests.post(query_url, data=params)
            response.raise_for_status()

            # Parse response
            result = {}
            for item in response.text.split('&'):
                key, value = item.split('=')
                result[key] = value

            logger.info(f"Queried payment status for order: {merchant_trade_no}")
            return result
        except Exception as e:
            logger.error(f"Failed to query payment: {str(e)}")
            return {}


import time
