"""
CryptoFastSignals - Indicator Tests
Unit tests for indicator calculations
"""

import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.indicator_calculator import (
    calculate_sma,
    detect_sma_crossover,
    calculate_atr,
    calculate_pivot_trend,
    check_volume_confirmation
)
from services.sr_detector import (
    calculate_pivot_points,
    get_high_low_levels,
    check_sr_proximity,
    get_sr_alignment
)
from services.signal_scorer import calculate_signal_score, get_score_rating


class TestSMACalculation:
    """Tests for SMA calculation"""
    
    def test_sma_basic(self):
        """Test basic SMA calculation"""
        closes = [10, 20, 30, 40, 50]
        sma = calculate_sma(closes, 3)
        
        # First 2 values should be None
        assert sma[0] is None
        assert sma[1] is None
        
        # SMA of 10, 20, 30 = 20
        assert sma[2] == 20.0
        
        # SMA of 20, 30, 40 = 30
        assert sma[3] == 30.0
        
        # SMA of 30, 40, 50 = 40
        assert sma[4] == 40.0
    
    def test_sma_single_value(self):
        """Test SMA with period 1"""
        closes = [10, 20, 30]
        sma = calculate_sma(closes, 1)
        
        assert sma == [10, 20, 30]


class TestSMACrossover:
    """Tests for SMA crossover detection"""
    
    def create_candles(self, closes):
        """Helper to create candle list from closes"""
        return [{"close": c, "high": c, "low": c, "open": c, "volume": 100} for c in closes]
    
    def test_long_crossover(self):
        """Test detection of bullish crossover"""
        # Fast SMA crosses above Slow SMA
        # Need enough data for SMA 21
        closes = [100] * 25  # Initialize with flat prices
        closes[-3] = 95  # Set up for crossover
        closes[-2] = 98
        closes[-1] = 105  # Fast now above slow
        
        candles = self.create_candles(closes)
        signal, details = detect_sma_crossover(candles)
        
        # Verify we got the details
        assert "sma_fast" in details
        assert "sma_slow" in details
    
    def test_insufficient_data(self):
        """Test with insufficient data"""
        candles = self.create_candles([100, 101, 102])
        signal, details = detect_sma_crossover(candles)
        
        assert signal is None
        assert "error" in details


class TestVolumeConfirmation:
    """Tests for volume confirmation"""
    
    def create_candles_with_volume(self, volumes):
        """Helper to create candles with specific volumes"""
        return [{"close": 100, "high": 100, "low": 100, "open": 100, "volume": v} for v in volumes]
    
    def test_high_volume_confirmation(self):
        """Test volume above threshold"""
        # 20 candles with volume 100, then 1 candle with volume 200
        volumes = [100] * 20 + [200]
        candles = self.create_candles_with_volume(volumes)
        
        confirmed, details = check_volume_confirmation(candles)
        
        assert confirmed is True
        assert details["volume_ratio"] == 2.0
    
    def test_low_volume_no_confirmation(self):
        """Test volume below threshold"""
        volumes = [100] * 20 + [100]  # Same as average
        candles = self.create_candles_with_volume(volumes)
        
        confirmed, details = check_volume_confirmation(candles)
        
        assert confirmed is False
        assert details["volume_ratio"] == 1.0


class TestPivotPoints:
    """Tests for Pivot Point calculation"""
    
    def test_pivot_calculation(self):
        """Test standard pivot point calculation"""
        daily_candles = [{
            "high": 110,
            "low": 90,
            "close": 100,
            "open": 95
        }]
        
        pivots = calculate_pivot_points(daily_candles)
        
        # PP = (H + L + C) / 3 = (110 + 90 + 100) / 3 = 100
        assert pivots["PP"] == 100
        
        # R1 = (2 * PP) - L = 200 - 90 = 110
        assert pivots["R1"] == 110
        
        # S1 = (2 * PP) - H = 200 - 110 = 90
        assert pivots["S1"] == 90


class TestSRProximity:
    """Tests for S/R proximity detection"""
    
    def test_near_resistance(self):
        """Test detection when price is near resistance"""
        sr_levels = {
            "resistances": [
                {"level": 100.4, "name": "R1", "source": "pivot"}
            ],
            "supports": [
                {"level": 98, "name": "S1", "source": "pivot"}
            ]
        }
        
        # Price at 100, R1 at 100.4 = 0.4% distance
        proximity = check_sr_proximity(100, sr_levels, threshold=0.005)
        
        assert proximity["zone"] == "RESISTANCE"
        assert proximity["at_resistance"] is True
    
    def test_near_support(self):
        """Test detection when price is near support"""
        sr_levels = {
            "resistances": [
                {"level": 102, "name": "R1", "source": "pivot"}
            ],
            "supports": [
                {"level": 99.6, "name": "S1", "source": "pivot"}
            ]
        }
        
        # Price at 100, S1 at 99.6 = 0.4% distance
        proximity = check_sr_proximity(100, sr_levels, threshold=0.005)
        
        assert proximity["zone"] == "SUPPORT"
        assert proximity["at_support"] is True


class TestSRAlignment:
    """Tests for S/R alignment logic"""
    
    def test_long_at_support_aligned(self):
        """Test LONG signal at support is aligned"""
        proximity = {"zone": "SUPPORT"}
        alignment, score = get_sr_alignment("LONG", proximity)
        
        assert alignment == "ALIGNED"
        assert score == 25
    
    def test_long_at_resistance_misaligned(self):
        """Test LONG signal at resistance is misaligned"""
        proximity = {"zone": "RESISTANCE"}
        alignment, score = get_sr_alignment("LONG", proximity)
        
        assert alignment == "MISALIGNED"
        assert score == -15
    
    def test_short_at_resistance_aligned(self):
        """Test SHORT signal at resistance is aligned"""
        proximity = {"zone": "RESISTANCE"}
        alignment, score = get_sr_alignment("SHORT", proximity)
        
        assert alignment == "ALIGNED"
        assert score == 25


class TestSignalScorer:
    """Tests for signal scoring"""
    
    def test_perfect_score(self):
        """Test maximum score with all confirmations"""
        result = calculate_signal_score(
            signal_direction="LONG",
            volume_confirmed=True,
            pivot_trend_direction="UP",
            sr_alignment="ALIGNED"
        )
        
        # 30 + 25 + 20 + 25 = 100
        assert result["score"] == 100
        assert result["confirmations"]["volume"] is True
        assert result["confirmations"]["pivot_trend"] is True
        assert result["confirmations"]["sr_aligned"] is True
    
    def test_sma_only_score(self):
        """Test minimum score with SMA only"""
        result = calculate_signal_score(
            signal_direction="LONG",
            volume_confirmed=False,
            pivot_trend_direction="DOWN",
            sr_alignment="NEUTRAL"
        )
        
        # 30 only
        assert result["score"] == 30
    
    def test_misaligned_penalty(self):
        """Test score with S/R misalignment penalty"""
        result = calculate_signal_score(
            signal_direction="LONG",
            volume_confirmed=True,
            pivot_trend_direction="UP",
            sr_alignment="MISALIGNED"
        )
        
        # 30 + 25 + 20 - 15 = 60
        assert result["score"] == 60
    
    def test_rating_levels(self):
        """Test score rating levels"""
        assert get_score_rating(95) == "EXCELLENT"
        assert get_score_rating(80) == "STRONG"
        assert get_score_rating(60) == "GOOD"
        assert get_score_rating(45) == "MODERATE"
        assert get_score_rating(30) == "WEAK"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
