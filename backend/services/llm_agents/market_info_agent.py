import requests
import json
import logging
from datetime import datetime
from typing import List, Dict, Any

from .base_agent import BaseAgent

class MarketInfoAgent(BaseAgent):
    """Agent that fetches market news and new pair listings using free sources.
    It uses Bybit public announcements endpoint and optional RSS feeds.
    Returns a list of dicts with keys: `title`, `url`, `published_at`, `type`.
    """

    BYBIT_ANNOUNCEMENTS_URL = "https://api.bybit.com/v5/market/announcement"
    DEFAULT_RSS_FEEDS = [
        "https://cointelegraph.com/rss",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
    ]

    def __init__(self, rss_feeds: List[str] = None):
        super().__init__(name="market_info_agent", role="Market News & Listing Monitor")
        self.logger = logging.getLogger(__name__)
        self.rss_feeds = rss_feeds or self.DEFAULT_RSS_FEEDS

    def _fetch_bybit_announcements(self) -> List[Dict]:
        try:
            resp = requests.get(self.BYBIT_ANNOUNCEMENTS_URL, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            # Expected structure: {"result": {"list": [...]}}
            announcements = data.get("result", {}).get("list", [])
            results = []
            for ann in announcements:
                results.append({
                    "title": ann.get("title", ""),
                    "url": ann.get("url", ""),
                    "published_at": ann.get("time", ""),
                    "type": "bybit",
                })
            return results
        except Exception as e:
            self.logger.error(f"[MarketInfoAgent] Error fetching Bybit announcements: {e}")
            return []

    def _fetch_rss(self) -> List[Dict]:
        results = []
        for feed_url in self.rss_feeds:
            try:
                resp = requests.get(feed_url, timeout=5)
                resp.raise_for_status()
                # Simple parsing: look for <item> entries using regex (lightweight)
                import re
                items = re.findall(r"<item>(.*?)</item>", resp.text, re.DOTALL)
                for item in items:
                    title_match = re.search(r"<title>(.*?)</title>", item, re.DOTALL)
                    link_match = re.search(r"<link>(.*?)</link>", item, re.DOTALL)
                    date_match = re.search(r"<pubDate>(.*?)</pubDate>", item, re.DOTALL)
                    results.append({
                        "title": title_match.group(1).strip() if title_match else "",
                        "url": link_match.group(1).strip() if link_match else "",
                        "published_at": date_match.group(1).strip() if date_match else "",
                        "type": "rss",
                    })
            except Exception as e:
                self.logger.error(f"[MarketInfoAgent] Error fetching RSS {feed_url}: {e}")
        return results

    def run(self, **kwargs) -> List[Dict]:
        """Collect and return market information.
        Optional kwargs:
            include_bybit (bool): default True
            include_rss (bool): default True
        """
        include_bybit = kwargs.get("include_bybit", True)
        include_rss = kwargs.get("include_rss", True)
        news = []
        if include_bybit:
            news.extend(self._fetch_bybit_announcements())
        if include_rss:
            news.extend(self._fetch_rss())
        # Sort by published_at descending if possible
        def _parse_date(item):
            try:
                return datetime.fromisoformat(item["published_at"]).timestamp()
            except Exception:
                return 0
        news.sort(key=_parse_date, reverse=True)
        return news

    def analyze(self, signal: Dict[str, Any], market_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes how market news affects a specific signal.
        For now, this is a placeholder that returns a neutral verdict.
        """
        news = self.run()
        # Basic logic: search for signal symbol in news titles
        symbol = signal.get("symbol", "").upper()
        relevant_news = [n for n in news if symbol in n["title"].upper()]
        
        return {
            "score": 50,
            "verdict": "NEUTRAL",
            "reasoning": f"Found {len(relevant_news)} news items for {symbol}. No major impact detected.",
            "metadata": {"news_count": len(relevant_news), "items": relevant_news[:3]}
        }
