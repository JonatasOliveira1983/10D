"""
10D - Bybit API Client
Handles all communication with Bybit API v5
"""

import requests
import time
import hashlib
import hmac
from typing import List, Dict, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BYBIT_BASE_URL, MIN_LEVERAGE, EXCLUDED_PAIRS

# API Keys from environment (optional for public endpoints)
BYBIT_API_KEY = os.environ.get("BYBIT_API_KEY", "")
BYBIT_API_SECRET = os.environ.get("BYBIT_API_SECRET", "")


class BybitClient:
    """Client for Bybit API v5"""
    
    def __init__(self):
        self.base_url = BYBIT_BASE_URL
        self.api_key = BYBIT_API_KEY
        self.api_secret = BYBIT_API_SECRET
        self.recv_window = "5000"
        self.session = requests.Session()
        
        # Real browser User-Agent to avoid 403
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        
        if self.api_key:
            print(f"[BYBIT] Auth enabled: {self.api_key[:8]}...", flush=True)
        else:
            print("[BYBIT] Auth disabled - using public mode", flush=True)
            
    def _generate_signature(self, timestamp: str, query_string: str) -> str:
        """Generate Bybit v5 API signature"""
        param_str = timestamp + self.api_key + self.recv_window + query_string
        hash = hmac.new(
            bytes(self.api_secret, "utf-8"),
            param_str.encode("utf-8"),
            hashlib.sha256
        )
        return hash.hexdigest()

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make a GET request to Bybit API with optional authentication"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            # Prepare headers
            headers = {}
            if self.api_key and self.api_secret:
                timestamp = str(int(time.time() * 1000))
                
                # Format query string for signature
                if params:
                    # Sort params to ensure consistent signature
                    import urllib.parse
                    sorted_params = sorted(params.items())
                    query_string = urllib.parse.urlencode(sorted_params)
                else:
                    query_string = ""
                
                signature = self._generate_signature(timestamp, query_string)
                
                headers.update({
                    "X-BAPI-API-KEY": self.api_key,
                    "X-BAPI-TIMESTAMP": timestamp,
                    "X-BAPI-RECV-WINDOW": self.recv_window,
                    "X-BAPI-SIGN": signature
                })
                print(f"[API] Auth GET {endpoint}", flush=True)
            else:
                print(f"[API] Public GET {endpoint} params={params}", flush=True)

            response = self.session.get(url, params=params, headers=headers, timeout=10)
            print(f"[API] {endpoint} -> HTTP {response.status_code}", flush=True)
            
            # If 403, log extra info
            if response.status_code == 403:
                print(f"[API] 403 FORBIDDEN - Bybit is blocking this IP. Try with API Keys.", flush=True)
                
            response.raise_for_status()
            data = response.json()
            
            if data.get("retCode") == 0:
                result = data.get("result", {})
                list_count = len(result.get("list", [])) if isinstance(result, dict) else 0
                print(f"[API] OK - {list_count} items", flush=True)
                return result
            else:
                print(f"[API] ERROR {data.get('retCode')}: {data.get('retMsg')}", flush=True)
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"[API] REQUEST FAILED: {e}", flush=True)
            return None
    
    def get_all_tickers(self, category: str = "linear") -> List[Dict]:
        """ Get all tickers for a category """
        result = self._make_request("/v5/market/tickers", {
            "category": category
        })
        
        if not result or not result.get("list"):
            return []
            
        return result["list"]

    def get_instruments(self, category: str = "linear") -> List[Dict]:
        """
        Get all perpetual instruments with leverage >= MIN_LEVERAGE
        Returns list of USDT perpetual pairs
        """
        result = self._make_request("/v5/market/instruments-info", {
            "category": category,
            "limit": 1000
        })
        
        if not result:
            return []
        
        instruments = result.get("list", [])
        
        # Filter for USDT perpetuals with sufficient leverage
        filtered = []
        for inst in instruments:
            symbol = inst.get("symbol", "")
            
            # Only USDT perpetuals
            if not symbol.endswith("USDT"):
                continue
            
            # Check leverage
            leverage_filter = inst.get("leverageFilter", {})
            max_leverage = float(leverage_filter.get("maxLeverage", "0"))
            
            if max_leverage >= MIN_LEVERAGE:
                filtered.append({
                    "symbol": symbol,
                    "baseCoin": inst.get("baseCoin", ""),
                    "quoteCoin": inst.get("quoteCoin", ""),
                    "maxLeverage": max_leverage,
                    "minPrice": inst.get("priceFilter", {}).get("minPrice", "0"),
                    "tickSize": inst.get("priceFilter", {}).get("tickSize", "0.01")
                })
        
        # Sort by symbol
        filtered.sort(key=lambda x: x["symbol"])
        
        print(f"[INSTRUMENTS] Found {len(filtered)} valid instruments (min leverage {MIN_LEVERAGE}x)", flush=True)
        return filtered
    
    def get_top_pairs(self, limit: int = 100) -> List[str]:
        """
        Get top N pairs by 24h volume, excluding specified pairs
        Returns list of symbols
        """
        print(f"[GET_TOP_PAIRS] Called with limit={limit}", flush=True)
        
        # Get 24h tickers for volume ranking
        result = self._make_request("/v5/market/tickers", {
            "category": "linear"
        })
        
        if not result:
            print("[GET_TOP_PAIRS] ERROR: tickers request failed", flush=True)
            return []
        
        tickers = result.get("list", [])
        print(f"[GET_TOP_PAIRS] Got {len(tickers)} tickers from API", flush=True)
        
        # Get instruments with sufficient leverage
        valid_instruments = {inst["symbol"] for inst in self.get_instruments()}
        
        # Filter and sort by volume
        usdt_tickers = []
        for ticker in tickers:
            symbol = ticker.get("symbol", "")
            
            # Skip excluded pairs
            if symbol in EXCLUDED_PAIRS:
                continue
                
            if symbol in valid_instruments and symbol.endswith("USDT"):
                volume_24h = float(ticker.get("turnover24h", "0"))
                usdt_tickers.append({
                    "symbol": symbol,
                    "volume24h": volume_24h,
                    "lastPrice": float(ticker.get("lastPrice", "0")),
                    "price24hPcnt": float(ticker.get("price24hPcnt", "0")) * 100
                })
        
        # Sort by 24h volume descending
        usdt_tickers.sort(key=lambda x: x["volume24h"], reverse=True)
        
        # Return top N symbols
        top_symbols = [t["symbol"] for t in usdt_tickers[:limit]]
        print(f"[GET_TOP_PAIRS] Returning {len(top_symbols)} pairs", flush=True)
        if top_symbols:
            print(f"[GET_TOP_PAIRS] First 5: {', '.join(top_symbols[:5])}", flush=True)
        return top_symbols
    
    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> List[Dict]:
        """
        Get kline/candlestick data
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            interval: Timeframe ("1", "5", "15", "30", "60", "240", "D", "W")
            limit: Number of candles to fetch
        
        Returns:
            List of candles with OHLCV data
        """
        result = self._make_request("/v5/market/kline", {
            "category": "linear",
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        })
        
        if not result:
            return []
        
        raw_klines = result.get("list", [])
        
        # Convert to structured format
        # Bybit returns: [timestamp, open, high, low, close, volume, turnover]
        candles = []
        for kline in reversed(raw_klines):  # Reverse to get chronological order
            candles.append({
                "timestamp": int(kline[0]),
                "open": float(kline[1]),
                "high": float(kline[2]),
                "low": float(kline[3]),
                "close": float(kline[4]),
                "volume": float(kline[5]),
                "turnover": float(kline[6])
            })
        
        return candles
    
    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """Get current ticker for a symbol"""
        result = self._make_request("/v5/market/tickers", {
            "category": "linear",
            "symbol": symbol
        })
        
        if not result or not result.get("list"):
            return None
        
        ticker = result["list"][0]
        return {
            "symbol": ticker.get("symbol"),
            "lastPrice": float(ticker.get("lastPrice", "0")),
            "bid": float(ticker.get("bid1Price", "0")),
            "ask": float(ticker.get("ask1Price", "0")),
            "volume24h": float(ticker.get("volume24h", "0")),
            "turnover24h": float(ticker.get("turnover24h", "0")),
            "price24hPcnt": float(ticker.get("price24hPcnt", "0")) * 100
        }

    def get_open_interest(self, symbol: str, interval: str, limit: int = 50) -> List[Dict]:
        """
        Get Open Interest history
        Interval: 5min, 15min, 30min, 1h, 4h, 1d
        """
        result = self._make_request("/v5/market/open-interest", {
            "category": "linear",
            "symbol": symbol,
            "intervalTime": interval,
            "limit": limit
        })
        
        if not result or not result.get("list"):
            return []
            
        return [{
            "openInterest": float(item["openInterest"]),
            "timestamp": int(item["timestamp"])
        } for item in result["list"]]

    def get_long_short_ratio(self, symbol: str, period: str, limit: int = 50) -> List[Dict]:
        """
        Get Long/Short Ratio history
        Period: 5min, 15min, 30min, 1h, 4h, 1d
        """
        result = self._make_request("/v5/market/account-ratio", {
            "category": "linear",
            "symbol": symbol,
            "period": period,
            "limit": limit
        })
        
        if not result or not result.get("list"):
            return []
            
        return [{
            "ratio": float(item["buyRatio"]), # Bybit v5 uses buyRatio
            "timestamp": int(item["timestamp"])
        } for item in result["list"]]

    def get_recent_trades(self, symbol: str, limit: int = 100) -> List[Dict]:
        """Get recent public trades for CVD calculation"""
        result = self._make_request("/v5/market/recent-trade", {
            "category": "linear",
            "symbol": symbol,
            "limit": limit
        })
        
        if not result or not result.get("list"):
            return []
            
        return [{
            "price": float(item["price"]),
            "size": float(item["size"]),
            "side": item["side"], # Buy or Sell
            "timestamp": int(item["time"])
        } for item in result["list"]]


# Test the client
if __name__ == "__main__":
    client = BybitClient()
    
    print("=" * 60)
    print("Testing Bybit Client")
    print("=" * 60)
    
    # Test get_top_pairs
    print("\n📊 Top 10 pairs by volume:")
    top_pairs = client.get_top_pairs(10)
    for i, symbol in enumerate(top_pairs, 1):
        print(f"  {i}. {symbol}")
    
    # Test get_klines
    if top_pairs:
        symbol = top_pairs[0]
        print(f"\n📈 Last 5 candles for {symbol} (30M):")
        klines = client.get_klines(symbol, "30", 5)
        for candle in klines:
            print(f"  Close: {candle['close']:.2f}, Volume: {candle['volume']:.2f}")
    
    # Test get_ticker
    if top_pairs:
        symbol = top_pairs[0]
        print(f"\n💰 Current ticker for {symbol}:")
        ticker = client.get_ticker(symbol)
        if ticker:
            print(f"  Price: ${ticker['lastPrice']:.2f}")
            print(f"  24h Change: {ticker['price24hPcnt']:.2f}%")
