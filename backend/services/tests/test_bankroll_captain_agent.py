import unittest
import sys
import os
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from backend.services.llm_agents.bankroll_captain_agent import BankrollCaptainAgent

class TestBankrollCaptainAgent(unittest.TestCase):
    def setUp(self):
        self.agent = BankrollCaptainAgent(max_exposure_pct=20.0, max_slots=10)
        self.total_bankroll = 10000.0

    def test_can_open_trade_within_limits(self):
        # 10% of bankroll = 1000, below 20% cap and slots available
        self.assertTrue(self.agent.can_open_trade(trade_amount=1000, total_bankroll=self.total_bankroll))

    def test_can_open_trade_exceeds_exposure(self):
        # 25% of bankroll = 2500, exceeds 20% cap
        self.assertFalse(self.agent.can_open_trade(trade_amount=2500, total_bankroll=self.total_bankroll))

    def test_can_open_trade_exceeds_slots(self):
        # Fill slots
        for i in range(10):
            self.agent.register_trade(f"trade{i}", {"amount": 100, "entry_price": 1, "stop_loss": 0.9})
        # Now slots full, should reject even small trade
        self.assertFalse(self.agent.can_open_trade(trade_amount=100, total_bankroll=self.total_bankroll))

    def test_register_and_deregister_trade(self):
        self.agent.register_trade("t1", {"amount": 500, "entry_price": 2, "stop_loss": 1.8})
        self.assertIn("t1", self.agent.active_trades)
        self.agent.deregister_trade("t1")
        self.assertNotIn("t1", self.agent.active_trades)

    def test_evaluate_break_even_moves_stop_loss(self):
        # Setup a trade with entry 100, stop loss 90, current price high enough
        self.agent.register_trade("t2", {"amount": 100, "entry_price": 100, "stop_loss": 90})
        # current price such that profit >= 1.5 * (entry - sl) => profit >= 1.5*10=15, so price >=115
        result = self.agent.evaluate_break_even("t2", current_price=120)
        self.assertTrue(result)
        self.assertEqual(self.agent.active_trades["t2"]["stop_loss"], 100)

    def test_evaluate_break_even_no_move(self):
        self.agent.register_trade("t3", {"amount": 100, "entry_price": 100, "stop_loss": 90})
        result = self.agent.evaluate_break_even("t3", current_price=105)  # profit 5 < 15
        self.assertFalse(result)
        self.assertEqual(self.agent.active_trades["t3"]["stop_loss"], 90)

    def test_analyze_approved(self):
        # 1000 / 10000 = 10% (under 20% limit)
        market_context = {"total_bankroll": 10000.0}
        result = self.agent.analyze({"amount": 1000}, market_context)
        self.assertEqual(result["verdict"], "APPROVED")
        self.assertEqual(result["score"], 100)

    def test_analyze_rejected(self):
        # 3000 / 10000 = 30% (over 20% limit)
        market_context = {"total_bankroll": 10000.0}
        result = self.agent.analyze({"amount": 3000}, market_context)
        self.assertEqual(result["verdict"], "REJECTED")
        self.assertEqual(result["score"], 0)

if __name__ == '__main__':
    unittest.main()
