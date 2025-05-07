from fastapi import FastAPI
from dotenv import load_dotenv
import os
from clients import KalshiHttpClient, Environment
from cryptography.hazmat.primitives import serialization
from fastapi import Query
import requests
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Load environment
load_dotenv()
env = Environment.PROD  # or DEMO if you prefer
KEYID = os.getenv('PROD_KEYID') or os.getenv('DEMO_KEYID')
KEYFILE = os.getenv('PROD_KEYFILE') or os.getenv('DEMO_KEYFILE')

# Load private key
with open(KEYFILE, "rb") as key_file:
    private_key = serialization.load_pem_private_key(
        key_file.read(),
        password=None,
    )

# Initialize Kalshi client
client = KalshiHttpClient(
    key_id=KEYID,
    private_key=private_key,
    environment=env
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/markets")
def get_active_markets():
    try:
        markets_response = client.get_markets()
        all_markets = markets_response.get("markets", [])
    except Exception as e:
        return {"error": str(e)}

    results = []

    for market in all_markets:
        # ✅ Only show active markets
        if market.get("status") != "active":
            continue

        # Include only minimal valid info to avoid errors
        results.append({
            "ticker": market.get("ticker"),
            "title": market.get("title"),
            "status": market.get("status"),
            "yes_bid": market.get("yes_bid"),
            "yes_ask": market.get("yes_ask"),
            "no_bid": market.get("no_bid"),
            "no_ask": market.get("no_ask"),
            "last_price": market.get("last_price"),
        })

    return {
        "count": len(results),
        "markets": results
    }

@app.get("/tickers")
def get_market_tickers():
    markets_response = client.get_markets()
    markets = markets_response.get("markets", [])

    return [
        {"title": m.get("title"), "ticker": m.get("ticker"), "status": m.get("status")}
        for m in markets
    ]

@app.get("/raw-market/{ticker}")
def get_raw_market(ticker: str):
    try:
        m = client.get_market(ticker)
        return m
    except Exception as e:
        return {"error": str(e)}


@app.get("/simple-market/{ticker}")
def get_simple_market(ticker: str):
    try:
        market_data = client.get_market(ticker).get("market", {})
        return {
            "ticker": market_data.get("ticker"),
            "title": market_data.get("title"),
            "yes_bid": market_data.get("yes_bid"),
            "yes_ask": market_data.get("yes_ask"),
            "no_bid": market_data.get("no_bid"),
            "no_ask": market_data.get("no_ask"),
            "last_price": market_data.get("last_price"),
            "status": market_data.get("status")
        }
    except Exception as e:
        return {"error": str(e)}

# Serve static files (HTML/JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    with open("static/dashboard.html", "r") as f:
        return f.read()
