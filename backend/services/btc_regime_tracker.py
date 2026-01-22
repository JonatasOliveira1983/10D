"""
BTC Regime Tracker Service
Detects BTC market regime (RANGING/TRENDING/BREAKOUT) and provides dynamic TP/SL targets.
Also calculates altcoin decoupling scores for ranging markets.
"""

from typing import Dict, List, Optional, Tuple
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    BTC_BB_WIDTH_RANGING, BTC_ATR_PCT_RANGING, BTC_TREND_EMA_DIST,
    BTC_BREAKOUT_VOLUME, BTC_BREAKOUT_ATR_EXPANSION,
    TP_RANGING, SL_RANGING, TP_TRENDING, SL_TRENDING, TP_BREAKOUT, SL_BREAKOUT,
    EMA_FAST_PERIOD, EMA_SLOW_PERIOD, BB_PERIOD, BB_STD_DEV, ATR_PERIOD
)
from services.indicator_calculator import (
    calculate_ema, calculate_atr, calculate_bollinger_bands, calculate_rsi
)


class BTCRegimeTracker:
    """
    Tracks BTC market regime and provides dynamic TP/SL recommendations.
    
    Regimes:
    - RANGING: Low volatility, price within tight range. TP: 1%, SL: 0.5%
    - TRENDING: Clear directional movement. TP: 2%, SL: 1%
    - BREAKOUT: Breaking key levels with volume. TP: 3%, SL: 1.5%
    """
    
    REGIMES = {
        "RANGING": {
            "tp": TP_RANGING,
            "sl": SL_RANGING,
            "priority": "decoupled_alts",
            "description": "BTC lateralizado, buscar alts independentes"
        },
        "TRENDING": {
            "tp": TP_TRENDING,
            "sl": SL_TRENDING,
            "priority": "trend_followers",
            "description": "BTC em tendência, seguir o fluxo"
        },
        "BREAKOUT": {
            "tp": TP_BREAKOUT,
            "sl": SL_BREAKOUT,
            "priority": "momentum",
            "description": "BTC rompendo níveis, aumentar alvos"
        },
        "SNIPER": {
            "tp": 0.06,  # Force 6%
            "sl": 0.01,  # 1% SL for sniper
            "priority": "sniper",
            "description": "MODO SNIPER: Alvo agressivo de 6%+"
        }
    }
    
    def __init__(self):
        self.current_regime = "TRENDING"  # Default
        self.regime_history = []  # Track regime changes
        self.last_24h_high = 0.0
        self.last_24h_low = 0.0
        self.last_24h_change = 0.0
        
    def detect_regime(
        self, 
        btc_candles_30m: List[Dict], 
        btc_candles_4h: Optional[List[Dict]] = None
    ) -> Tuple[str, Dict]:
        """
        Detect current BTC market regime.
        
        Args:
            btc_candles_30m: 30-minute BTC candles (at least 50)
            btc_candles_4h: 4-hour BTC candles (optional, for confirmation)
            
        Returns:
            Tuple of (regime_name, details_dict)
        """
        if not btc_candles_30m or len(btc_candles_30m) < 50:
            return self.current_regime, {"error": "Not enough BTC data"}
        
        closes = [c["close"] for c in btc_candles_30m]
        highs = [c["high"] for c in btc_candles_30m]
        lows = [c["low"] for c in btc_candles_30m]
        volumes = [c["volume"] for c in btc_candles_30m]
        current_price = closes[-1]
        
        # Calculate indicators
        ema_fast = calculate_ema(closes, EMA_FAST_PERIOD)
        ema_slow = calculate_ema(closes, EMA_SLOW_PERIOD)
        atr_values = calculate_atr(btc_candles_30m, ATR_PERIOD)
        bb_data = calculate_bollinger_bands(closes, BB_PERIOD, BB_STD_DEV)
        
        current_ema_fast = ema_fast[-1] if ema_fast[-1] else current_price
        current_ema_slow = ema_slow[-1] if ema_slow[-1] else current_price
        current_atr = atr_values[-1] if atr_values[-1] else 0
        current_bb_upper = bb_data["upper"][-1] if bb_data["upper"][-1] else current_price * 1.02
        current_bb_lower = bb_data["lower"][-1] if bb_data["lower"][-1] else current_price * 0.98
        
        # Calculate metrics
        bb_width = (current_bb_upper - current_bb_lower) / current_price
        atr_pct = current_atr / current_price if current_price > 0 else 0
        ema_distance = abs(current_ema_fast - current_ema_slow) / current_ema_slow if current_ema_slow > 0 else 0
        
        # 24h High/Low (last 48 candles = 24h in 30m timeframe)
        lookback_24h = min(48, len(btc_candles_30m))
        high_24h = max(highs[-lookback_24h:])
        low_24h = min(lows[-lookback_24h:])
        self.last_24h_high = high_24h
        self.last_24h_low = low_24h
        
        # Volume analysis
        avg_volume = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else sum(volumes) / len(volumes)
        current_volume = volumes[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        # ATR expansion check (current ATR vs average of last 10 periods)
        avg_atr = sum([a for a in atr_values[-10:] if a]) / 10 if any(atr_values[-10:]) else current_atr
        atr_expansion = current_atr / avg_atr if avg_atr > 0 else 1
        
        # Calculate 24h change
        price_24h_ago = btc_candles_30m[-lookback_24h]["close"]
        price_change_24h = (current_price - price_24h_ago) / price_24h_ago if price_24h_ago > 0 else 0
        self.last_24h_change = price_change_24h

        details = {
            "bb_width": round(bb_width * 100, 3),  # As percentage
            "atr_pct": round(atr_pct * 100, 3),    # As percentage
            "ema_distance": round(ema_distance * 100, 3),  # As percentage
            "volume_ratio": round(volume_ratio, 2),
            "atr_expansion": round(atr_expansion, 2),
            "high_24h": round(high_24h, 2),
            "low_24h": round(low_24h, 2),
            "current_price": round(current_price, 2),
            "price_change_24h": round(price_change_24h * 100, 2)
        }
        
        # === REGIME DETECTION LOGIC ===
        
        # 1. Check for BREAKOUT first (highest priority)
        is_breaking_high = current_price > high_24h * 0.998  # Within 0.2% of 24h high
        is_breaking_low = current_price < low_24h * 1.002   # Within 0.2% of 24h low
        is_high_volume = volume_ratio >= BTC_BREAKOUT_VOLUME
        is_atr_expanding = atr_expansion >= BTC_BREAKOUT_ATR_EXPANSION
        
        if (is_breaking_high or is_breaking_low) and (is_high_volume or is_atr_expanding):
            details["trigger"] = "breakout"
            details["breakout_direction"] = "UP" if is_breaking_high else "DOWN"
            self.current_regime = "BREAKOUT"
            return "BREAKOUT", details
        
        # 2. Check for RANGING (tight Bollinger Bands + low ATR)
        is_bb_tight = bb_width < BTC_BB_WIDTH_RANGING
        is_low_volatility = atr_pct < BTC_ATR_PCT_RANGING
        is_ema_flat = ema_distance < BTC_TREND_EMA_DIST
        
        if is_bb_tight and is_low_volatility:
            details["trigger"] = "ranging"
            self.current_regime = "RANGING"
            return "RANGING", details
        
        # 3. Default to TRENDING
        if ema_distance >= BTC_TREND_EMA_DIST:
            details["trigger"] = "trending"
            details["trend_direction"] = "UP" if current_ema_fast > current_ema_slow else "DOWN"
            self.current_regime = "TRENDING"
            return "TRENDING", details
        
        # Fallback
        details["trigger"] = "default"
        self.current_regime = "TRENDING"
        return "TRENDING", details
    
    def calculate_decoupling_score(
        self, 
        alt_candles: List[Dict], 
        btc_candles: List[Dict],
        lookback: int = 20
    ) -> float:
        """
        Calculate how much an altcoin is moving independently from BTC.
        
        High score (>0.5) = Alt is moving on its own (good for RANGING regime)
        Low score (<0.5) = Alt follows BTC closely
        
        Args:
            alt_candles: Altcoin candles
            btc_candles: BTC candles
            lookback: Number of candles to analyze
            
        Returns:
            Decoupling score between 0.0 and 1.0
        """
        if not alt_candles or not btc_candles:
            return 0.0
        if len(alt_candles) < lookback or len(btc_candles) < lookback:
            return 0.0
        
        try:
            alt_changes = []
            btc_changes = []
            
            for i in range(-lookback, 0):
                alt_change = (alt_candles[i]["close"] - alt_candles[i-1]["close"]) / alt_candles[i-1]["close"]
                btc_change = (btc_candles[i]["close"] - btc_candles[i-1]["close"]) / btc_candles[i-1]["close"]
                alt_changes.append(alt_change)
                btc_changes.append(btc_change)
            
            # Calculate correlation
            n = len(alt_changes)
            if n == 0:
                return 0.0
                
            # Mean
            alt_mean = sum(alt_changes) / n
            btc_mean = sum(btc_changes) / n
            
            # Covariance and standard deviations
            covariance = sum((a - alt_mean) * (b - btc_mean) for a, b in zip(alt_changes, btc_changes)) / n
            alt_std = (sum((a - alt_mean) ** 2 for a in alt_changes) / n) ** 0.5
            btc_std = (sum((b - btc_mean) ** 2 for b in btc_changes) / n) ** 0.5
            
            if alt_std == 0 or btc_std == 0:
                return 0.5  # Neutral if no movement
            
            # Pearson correlation (-1 to 1)
            correlation = covariance / (alt_std * btc_std)
            
            # Convert to decoupling score (0 to 1)
            # correlation = 1 (perfectly correlated) -> decoupling = 0
            # correlation = 0 (no correlation) -> decoupling = 0.5
            # correlation = -1 (inversely correlated) -> decoupling = 1
            decoupling_score = (1 - correlation) / 2
            
            # Also consider if alt is outperforming
            alt_total_change = sum(alt_changes)
            btc_total_change = sum(btc_changes)
            
            # Bonus if alt is gaining while BTC is flat/down
            if btc_total_change < 0.01 and alt_total_change > 0.02:  # BTC flat, alt up
                decoupling_score = min(1.0, decoupling_score + 0.2)
            
            return round(min(1.0, max(0.0, decoupling_score)), 3)
            
        except Exception as e:
            print(f"[BTC REGIME] Error calculating decoupling: {e}", flush=True)
            return 0.0
    
    def get_dynamic_targets(self, regime: str = None, force_sniper: bool = False) -> Tuple[float, float]:
        """
        Get TP and SL percentages based on current regime.
        
        Args:
            regime: Override regime (uses current if None)
            force_sniper: If True, returns sniper targets (6%)
            
        Returns:
            Tuple of (tp_percent, sl_percent)
        """
        if force_sniper:
            config = self.REGIMES["SNIPER"]
            return config["tp"], config["sl"]
            
        regime = regime or self.current_regime
        config = self.REGIMES.get(regime, self.REGIMES["TRENDING"])
        return config["tp"], config["sl"]
    
    def get_regime_info(self) -> Dict:
        """Get full info about current regime"""
        config = self.REGIMES.get(self.current_regime, self.REGIMES["TRENDING"])
        return {
            "regime": self.current_regime,
            "tp_pct": config["tp"] * 100,
            "sl_pct": config["sl"] * 100,
            "priority": config["priority"],
            "description": config["description"],
            "high_24h": self.last_24h_high,
            "low_24h": self.last_24h_low,
            "change_24h": round(self.last_24h_change * 100, 2)
        }


# Quick test
if __name__ == "__main__":
    tracker = BTCRegimeTracker()
    print("BTC Regime Tracker initialized")
    print(f"Default regime: {tracker.current_regime}")
    print(f"Default TP/SL: {tracker.get_dynamic_targets()}")
