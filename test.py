import requests

# Replace with your actual values
WALLET_ADDRESS = "0x24204bBA329Cacb6391B8687fc9578D00D618a01"
CONTRACT_ADDRESS = "0x082EF77013B51F4a808e83a4D345CdC88CfdD9C4"  # JAXIM token
COVALENT_API_KEY = "your-api-key-here"

url = (
    f"https://api.covalenthq.com/v1/base-mainnet/address/"
    f"{WALLET_ADDRESS}/balances_v2/?contract-address={CONTRACT_ADDRESS}&key={COVALENT_API_KEY}"
)

response = requests.get(url)
data = response.json()

# Check if the response is successful
if not data.get("error"):
    items = data["data"]["items"]
    for item in items:
        if item["contract_address"].lower() == CONTRACT_ADDRESS.lower():
            balance_wei = int(item["balance"])
            decimals = item["contract_decimals"]
            symbol = item["contract_ticker_symbol"]
            balance = balance_wei / (10 ** decimals)
            print(f"{symbol} Balance: {balance}")
else:
    print("Error:", data.get("error_message"))
