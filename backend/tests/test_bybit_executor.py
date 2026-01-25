import unittest
from unittest.mock import patch
from backend.services.bybit_executor import place_test_order, execute_signals

class TestBybitExecutor(unittest.TestCase):
    @patch('backend.services.bybit_executor.client')
    def test_place_test_order_market(self, mock_client):
        mock_client.place_order.return_value = {"retCode": 0, "result": {"orderId": "123"}}
        signal = {"symbol": "BTCUSDT", "side": "Buy", "qty": 0.001}
        resp = place_test_order(signal)
        self.assertEqual(resp["retCode"], 0)
        mock_client.place_order.assert_called_once()

    @patch('backend.services.bybit_executor.client')
    def test_execute_multiple(self, mock_client):
        mock_client.place_order.return_value = {"retCode": 0}
        signals = [
            {"symbol": "BTCUSDT", "side": "Buy", "qty": 0.001},
            {"symbol": "ETHUSDT", "side": "Sell", "qty": 0.01, "price": 1200}
        ]
        results = execute_signals(signals)
        self.assertEqual(len(results), 2)
        for r in results:
            self.assertIn("response", r)
            self.assertEqual(r["response"]["retCode"], 0)

if __name__ == "__main__":
    unittest.main()
