from .exchange_interface import ExchangeInterface
import requests
import os
from dotenv import load_dotenv
load_dotenv()

binance_klines_base_url = os.getenv("BINANCE_KLINES_BASE_URL", "https://api.binance.com")
binance_klines_endpoint = os.getenv("BINANCE_KLINES_ENDPOINT", "/api/v3/klines")

class BinanceExchange(ExchangeInterface):
    def __init__(self):
        self=self

    async def get_market_data(self, ticker: str, interval: str, limit: int, timeout=10):
        url = f"{binance_klines_base_url}{binance_klines_endpoint}"

        params = {
            "symbol": ticker,
            "interval": interval,
            "limit": limit
        }

        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as http_err:
            raise Exception(f"[HTTP Error] Status code: {response.status_code} | Message: {response.text}") from http_err
        
        except requests.exceptions.RequestException as req_err:
            raise Exception(f"[Request Error] Unable to fetch data from Binance: {req_err}") from req_err

    