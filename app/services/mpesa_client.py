"""It establishes an interface with Safaricom's Daraja gateway.
 It auto-generates the required base64 authentication tokens, 
 securely pieces together the transaction passwords using timestamps,
and converts customer numbers into standard Kenyan country code formats (254XXXXXXXXX)
 before triggering an STK Push."""

import os
import base64
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class MpesaClient:
    def __init__(self):
        self.consumer_key = os.getenv("MPESA_CONSUMER_KEY")
        self.consumer_secret = os.getenv("MPESA_CONSUMER_SECRET")
        self.shortcode = os.getenv("MPESA_SHORTCODE")
        self.passkey = os.getenv("MPESA_PASSKEY")
        self.callback_url = os.getenv("MPRESA_CALLBACK_URL")
        self.base_url = "https://safaricom.co.ke"

    def get_access_token(self) -> str:
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        credentials = f"{self.consumer_key}:{self.consumer_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {"Authorization": f"Basic {encoded_credentials}"}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json().get("access_token")
        raise Exception(f"Failed to fetch M-Pesa token: {response.text}")

    def generate_password(self, timestamp: str) -> str:
        data_to_encode = f"{self.shortcode}{self.passkey}{timestamp}"
        return base64.b64encode(data_to_encode.encode()).decode()

    def initiate_stk_push(self, phone_number: str, amount: int, account_reference: str) -> dict:
        access_token = self.get_access_token()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password = self.generate_password(timestamp)
        
        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        
        if phone_number.startswith("0"):
            phone_number = "254" + phone_number[1:]
        elif phone_number.startswith("+"):
            phone_number = phone_number.replace("+", "")

        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone_number,
            "PartyB": self.shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": self.callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": "IngoEats Food & Liquor Delivery"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        return response.json()
