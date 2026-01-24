import unittest
import sys
import os
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from unittest.mock import patch, MagicMock
from backend.services.llm_agents.market_info_agent import MarketInfoAgent

class TestMarketInfoAgent(unittest.TestCase):
    @patch('backend.services.llm_agents.market_info_agent.requests.get')
    def test_fetch_bybit_announcements(self, mock_get):
        # Mock response for Bybit announcements
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "result": {
                "list": [
                    {"title": "New Pair XYZ", "url": "https://bybit.com/xyz", "time": "2026-01-24T00:00:00Z"}
                ]
            }
        }
        mock_get.return_value = mock_resp
        agent = MarketInfoAgent()
        result = agent._fetch_bybit_announcements()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "New Pair XYZ")
        self.assertEqual(result[0]["type"], "bybit")

    @patch('backend.services.llm_agents.market_info_agent.requests.get')
    def test_fetch_rss(self, mock_get):
        # Mock RSS feed response (simple XML with one item)
        rss_xml = """<rss><channel><item><title>Crypto News</title><link>https://example.com/news</link><pubDate>Mon, 24 Jan 2026 01:00:00 GMT</pubDate></item></channel></rss>"""
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.text = rss_xml
        mock_get.return_value = mock_resp
        agent = MarketInfoAgent(rss_feeds=["https://example.com/rss"])
        result = agent._fetch_rss()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Crypto News")
        self.assertEqual(result[0]["type"], "rss")

    def test_run_combines_sources(self):
        # Use real methods but patch both internal fetchers
        with patch.object(MarketInfoAgent, '_fetch_bybit_announcements', return_value=[{"title": "Bybit", "url": "u", "published_at": "t", "type": "bybit"}]), \
             patch.object(MarketInfoAgent, '_fetch_rss', return_value=[{"title": "RSS", "url": "u", "published_at": "t", "type": "rss"}]):
            agent = MarketInfoAgent()
            news = agent.run()
            self.assertEqual(len(news), 2)
            self.assertTrue(any(item["type"] == "bybit" for item in news))
            self.assertTrue(any(item["type"] == "rss" for item in news))

    def test_analyze_relevant_news(self):
        with patch.object(MarketInfoAgent, 'run', return_value=[{"title": "BTC is up", "url": "u", "published_at": "t", "type": "rss"}]):
            agent = MarketInfoAgent()
            result = agent.analyze({"symbol": "BTC"}, {})
            self.assertEqual(result["verdict"], "NEUTRAL")
            self.assertEqual(result["metadata"]["news_count"], 1)

if __name__ == '__main__':
    unittest.main()
