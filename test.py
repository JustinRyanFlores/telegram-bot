# test_balance.py

import os
import requests
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Constants
COVALENT_API_KEY = os.getenv("COVALENT_API_KEY")
COVALENT_BASE_URL = "https://api.covalenthq.com/v1"
CHAIN_NAME = "base-mainnet"
JAXIM_CONTRACT = "0x082Ef77013B51f4a808e83a4D345CdC88CfdD9C4"
BOT_WALLET = os.getenv("BOT_WALLET").lower()

def get_tokens_sent(wallet):
    try:
        wallet = wallet.lower()

        # Call Covalent API to get transfers of this wallet for the given token
        transfer_url = f"{COVALENT_BASE_URL}/{CHAIN_NAME}/address/{wallet}/transfers_v2/"
        transfer_params = {
            "contract-address": JAXIM_CONTRACT,
            "key": COVALENT_API_KEY
        }

        response = requests.get(transfer_url, params=transfer_params)
        if response.status_code != 200:
            print(f"⚠️ API Error: {response.status_code} - {response.text}")
            return None

        data = response.json()
        if data.get("error"):
            print(f"❌ API Error: {data.get('error_message')}")
            return None

        total_sent = 0
        for item in data["data"]["items"]:
            for transfer in item["transfers"]:
                if (
                    transfer["from_address"].lower() == wallet
                    and transfer["to_address"].lower() == BOT_WALLET
                ):
                    delta = int(transfer["delta"])
                    decimals = transfer["contract_decimals"]
                    total_sent += delta / (10 ** decimals)

        return int(total_sent)

    except Exception as e:
        print("❌ Exception:", str(e))
        return None

# --------- Test the function ---------
if __name__ == "__main__":
    # Replace with any wallet you want to test
    test_wallet = "0xb51d60Cb8d3768874588610c93169A5b5b69f9A9"
    
    sent = get_tokens_sent(test_wallet)
    
    if sent is not None:
        print(f"✅ Tokens sent from {test_wallet} to bot: {sent} JXJ")
    else:
        print("❌ Could not fetch token transfer data.")
