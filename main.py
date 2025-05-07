import os
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization
import asyncio

from clients import KalshiHttpClient, KalshiWebSocketClient, Environment

# Load environment variables
load_dotenv(dotenv_path=".env")
env = Environment.PROD # toggle environment here
KEYID = os.getenv('DEMO_KEYID') if env == Environment.DEMO else os.getenv('PROD_KEYID')
KEYFILE = os.getenv('DEMO_KEYFILE') if env == Environment.DEMO else os.getenv('PROD_KEYFILE')

try:
    with open(KEYFILE, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None  # Provide the password if your key is encrypted
        )
except FileNotFoundError:
    raise FileNotFoundError(f"Private key file not found at {KEYFILE}")
except Exception as e:
    raise Exception(f"Error loading private key: {str(e)}")

# Initialize the HTTP client
client = KalshiHttpClient(
    key_id=KEYID,
    private_key=private_key,
    environment=env
)

# Get account balance
balance = client.get_balance()
print("Balance:", balance)

from tabulate import tabulate

# Fetch all active markets
markets_response = client.get_markets()
markets = markets_response.get("markets", [])

# Collect table rows
table_rows = []

for market in markets[:10]:  # limit to first 10 markets for now
    market_ticker = market.get("ticker")
    market_title = market.get("title")

    # Fetch market details
    market_details = client.get_market(market_ticker)
    for contract in market_details.get("contracts", []):
        row = [
            market_title,
            contract.get("ticker"),
            contract.get("last_price"),
            contract.get("yes_bid"),
            contract.get("yes_ask"),
            contract.get("no_bid"),
            contract.get("no_ask")
        ]
        table_rows.append(row)

# Define table headers
headers = ["Market", "Outcome", "Last Price", "Yes Bid", "Yes Ask", "No Bid", "No Ask"]

# Print table
print(tabulate(table_rows, headers=headers, tablefmt="pretty"))

# Initialize the WebSocket client
ws_client = KalshiWebSocketClient(
    key_id=KEYID,
    private_key=private_key,
    environment=env
)

# Connect via WebSocket
#asyncio.run(ws_client.connect())