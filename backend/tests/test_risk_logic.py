import sys
import unittest
from unittest.mock import MagicMock
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.bankroll_manager import BankrollManager

class MockDB:
    def __init__(self):
        self.client = MagicMock()
        # Mocking table().select().eq().execute().data
        self.mock_trades = []
        
    def set_open_trades(self, trades):
        self.mock_trades = trades
    
    # Simple simulation of the chain: client.table().select().eq().execute()
    # Logic: return self.mock_trades
    
    pass

class TestRiskManagement(unittest.TestCase):
    def setUp(self):
        self.db = MockDB()
        self.manager = BankrollManager(self.db)
        # Mock database chain
        self.manager.db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        # Override initial status for tests
        self.manager.get_status = MagicMock(return_value={
            "current_balance": 20.0,
            "entry_size_usd": 1.0, # 5% of 20
        })

    def test_risk_cap_initial(self):
        """Test blocking after 4 trades (20% logic) without Risk-Free"""
        # Scenario: 4 trades open, all risky
        open_trades = [
            {"entry_price": 100, "stop_loss": 99, "direction": "LONG", "entry_size_usd": 1.0},
            {"entry_price": 100, "stop_loss": 99, "direction": "LONG", "entry_size_usd": 1.0},
            {"entry_price": 100, "stop_loss": 99, "direction": "LONG", "entry_size_usd": 1.0},
            {"entry_price": 100, "stop_loss": 99, "direction": "LONG", "entry_size_usd": 1.0},
        ]
        
        # Mock DB response
        self.manager.db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = open_trades
        
        status = self.manager.get_status()
        allowed, reason = self.manager._check_risk_exposure(status)
        
        print(f"\n[TEST 1] 4 Risky Trades ($4 exposure / $4 cap) -> Attempt 5th: {allowed} ({reason})")
        self.assertFalse(allowed, "Should block 5th trade when risk cap is hit")

    def test_risk_free_scaling(self):
        """Test unlocking slot when 1 trade becomes Risk-Free"""
        # Scenario: 4 trades open, BUT 1 is Risk-Free (SL >= Entry)
        open_trades = [
            {"entry_price": 100, "stop_loss": 100, "direction": "LONG", "entry_size_usd": 1.0}, # Risk Free!
            {"entry_price": 100, "stop_loss": 99, "direction": "LONG", "entry_size_usd": 1.0},
            {"entry_price": 100, "stop_loss": 99, "direction": "LONG", "entry_size_usd": 1.0},
            {"entry_price": 100, "stop_loss": 99, "direction": "LONG", "entry_size_usd": 1.0},
        ]
        
        self.manager.db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = open_trades
        
        status = self.manager.get_status()
        allowed, reason = self.manager._check_risk_exposure(status)
        
        print(f"\n[TEST 2] 3 Risky + 1 Risk-Free ($3 exposure / $4 cap) -> Attempt 5th: {allowed} ({reason})")
        self.assertTrue(allowed, "Should allow 5th trade when exposure drops below cap")

    def test_max_slots(self):
        """Test HArd Max 10 Slots"""
        # Scenario: 10 Trades, ALL Risk Free (Extreme case)
        open_trades = [{"entry_price": 100, "stop_loss": 101, "direction": "LONG", "entry_size_usd": 1.0}] * 10
        
        self.manager.db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = open_trades
        
        status = self.manager.get_status()
        allowed, reason = self.manager._check_risk_exposure(status)
        
        print(f"\n[TEST 3] 10 Risk-Free Trades (Slots Full) -> Attempt 11th: {allowed} ({reason})")
        self.assertFalse(allowed, "Should block 11th trade due to Max Slots")


if __name__ == '__main__':
    unittest.main()
