
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add backend to path - FIX: Ensure we are pointing to the backend root
import pathlib
backend_path = str(pathlib.Path(__file__).parent.parent.absolute())
if backend_path not in sys.path:
    sys.path.append(backend_path)

from services.signal_generator import SignalGenerator
from config import SNIPER_DECOUPLING_THRESHOLD

class TestRangingLogic(unittest.TestCase):
    def setUp(self):
        # Mock dependencies to avoid DB/API calls
        with patch('services.signal_generator.DatabaseManager'), \
             patch('services.signal_generator.BybitClient'), \
             patch('services.signal_generator.MLPredictor'), \
             patch('services.signal_generator.BTCRegimeTracker') as MockTracker:
            
            self.generator = SignalGenerator()
            self.generator.btc_tracker = MockTracker.return_value
            self.generator.ml_predictor = None # Disable ML for this test
            
    def test_ranging_regime_filtering(self):
        """Test that ONLY decoupled signals are accepted in RANGING regime"""
        
        # Setup: Force Regime to RANGING
        self.generator.current_btc_regime = "RANGING"
        
        # Mock analyze_pair to return a base valid signal
        base_signal = {
            "symbol": "TESTUSDT",
            "score": 100, # Max score
            "direction": "LONG",
            "type": "EMA_CROSSOVER",
            "entry_price": 100,
            "stop_loss": 99,
            "take_profit": 102,
            # ... other required fields mock ...
            "score_result": {"confirmations": {}, "breakdown": {}},
            "sr_alignment": "NEUTRAL",
            "pivot_trend": "UP",
            "institutional_details": {}
        }
        
        # Scenario 1: Low Decoupling (Should be REJECTED)
        # We need to mock how analyze_pair returns the signal with decoupling_score
        # Since analyze_pair calculates it internally, we'll mock the internal call or property 
        # But simpler: we can inspect the `scan_all_pairs` loop logic logic directly if we could extract it,
        # or we invoke the logic block we want to test.
        # Given existing code structure, `analyze_pair` computes decoupling.
        # Let's mock `analyze_pair` entirely to return our prepared signal.
        
        # Note: In the actual code `scan_all_pairs` calls `analyze_pair`, which returns a signal. 
        # The FILTERING happens inside `scan_all_pairs`.
        
        # 1. Low Decoupling
        low_decoupling_signal = base_signal.copy()
        low_decoupling_signal["decoupling_score"] = 0.2
        
        # 2. High Decoupling
        high_decoupling_signal = base_signal.copy()
        high_decoupling_signal["decoupling_score"] = 0.8
        
        # We will mock analyze_pair to return these sequentially
        self.generator.analyze_pair = MagicMock(side_effect=[low_decoupling_signal, high_decoupling_signal])
        self.generator.monitored_pairs = ["LOW_DECOUPLED", "HIGH_DECOUPLED"]
        
        # Capture print output to verify logic (since logic prints "[SNIPER FILTER] ... REJECTED")
        from io import StringIO
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            self.generator.scan_all_pairs()
        except Exception as e:
            # Ignore errors unrelated to logic (like DB access)
            pass
            
        sys.stdout = sys.__stdout__ # Reset stdout
        output = captured_output.getvalue()
        
        print("\n=== TEST OUTPUT ===")
        print(output)
        print("===================\n")
        
        # ASSERTIONS
        self.assertIn("REJECTED: Low decoupling", output, "Should reject signal with low decoupling in Ranging")
        self.assertNotIn("REJECTED: Low decoupling (0.8)", output, "Should NOT reject signal with high decoupling")
        
if __name__ == '__main__':
    unittest.main()
