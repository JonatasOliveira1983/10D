"""
10D - Bybit API Client
Handles all communication with Bybit API v5
"""

import requests
import time
from typing import List, Dict, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BYBIT_BASE_URL, MIN_LEVERAGE, EXCLUDED_PAIRS


class BybitClient:
    """Client for Bybit API v5"""
    
    def __init__(self):
        self.base_url = BYBIT_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make a GET request to Bybit API"""
        try:
            url = f"{self.base_url}{endpoint}"
            print(f"📡 API Request: {url} params={params}", flush=True)
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("retCode") == 0:
                result = data.get("result", {})
                list_count = len(result.get("list", [])) if isinstance(result, dict) else 0
                print(f"✅ API Response OK: {list_count} items", flush=True)
                return result
            else:
                print(f"❌ API Error: {data.get('retMsg', 'Unknown error')}", flush=True)
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}", flush=True)
            return None
    
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
        
        print(f"🛠️ get_instruments: Found {len(filtered)} valid instruments (min leverage {MIN_LEVERAGE}x)", flush=True)
        return filtered
    
    def get_top_pairs(self, limit: int = 100) -> List[str]:
        """
        Get top N pairs by 24h volume, excluding specified pairs
        Returns list of symbols
        """
        print(f"🔄 get_top_pairs called with limit={limit}", flush=True)
        
        # Get 24h tickers for volume ranking
        result = self._make_request("/v5/market/tickers", {
            "category": "linear"
        })
        
        if not result:
            print("❌ get_top_pairs: tickers request failed", flush=True)
            return []
        
        tickers = result.get("list", [])
        print(f"📊 Got {len(tickers)} tickers from API", flush=True)
        
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
        print(f"✅ get_top_pairs: Returning {len(top_symbols)} pairs", flush=True)
        if top_symbols:
            print(f"📋 First 5: {', '.join(top_symbols[:5])}", flush=True)
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
