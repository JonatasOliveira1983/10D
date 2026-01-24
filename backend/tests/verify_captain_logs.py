import sys
import os
import unittest
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.bankroll_manager import BankrollManager

class TestCaptainLogs(unittest.TestCase):
    def test_log_callback_wiring(self):
        print("Testing Captain Logs Wiring...")
        
        # Mock dependencies
        mock_db = MagicMock()
        mock_callback = MagicMock()
        mock_llm = MagicMock()
        
        # Initialize BankrollManager with the new wiring
        manager = BankrollManager(
            db_manager=mock_db,
            log_callback=mock_callback,
            llm_brain=mock_llm
        )
        
        # Verify wiring matches
        self.assertEqual(manager.log_callback, mock_callback)
        self.assertEqual(manager.llm_brain, mock_llm)
        print("[OK] Dependencies wired correctly")
        
        # Test simulation of opening a trade (triggering a log)
        # We mock the _open_trade logic slightly to isolate the log call
        # But better to call the actual method if we mock DB insert
        
        signal = {
            "symbol": "BTCUSDT",
            "entry_price": 50000,
            "stop_loss": 49000,
            "direction": "LONG",
            "score": 85
        }
        status = {"entry_size_usd": 10.0, "current_balance": 100.0}
        
        # Call internal open_trade
        manager._open_trade(signal, status)
        
        # Verify callback was called
        mock_callback.assert_called()
        call_args = mock_callback.call_args
        print(f"[OK] Callback triggered with: {call_args}")
        
        agent_id = call_args[0][0]
        event_type = call_args[0][1]
        
        self.assertEqual(agent_id, "bankroll_captain_agent")
        self.assertEqual(event_type, "TRADE_OPEN")
        print("[SUCCESS] Captain is speaking to the UI!")

if __name__ == "__main__":
    unittest.main()
