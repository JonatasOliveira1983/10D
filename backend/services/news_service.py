import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import threading
import time

class NewsService:
    def __init__(self, cache_ttl_minutes=15):
        self.rss_feeds = [
            "https://cointelegraph.com/rss",
            "https://www.coindesk.com/arc/outboundfeeds/rss/"
        ]
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self.cached_headlines = []
        self.last_fetch_time = None
        self._lock = threading.Lock()
        print("[NewsService] Initialized with feeds:", self.rss_feeds)

    def get_latest_headlines(self, limit=20):
        """Returns the latest headlines, using cache if valid."""
        with self._lock:
            now = datetime.now()
            if self.last_fetch_time and (now - self.last_fetch_time) < self.cache_ttl:
                # Cache hit
                return self.cached_headlines[:limit]
        
        # Cache miss or expired - fetch fresh news
        return self._fetch_all_headlines(limit)

    def _fetch_all_headlines(self, limit):
        all_news = []
        for url in self.rss_feeds:
            try:
                # Use a proper User-Agent to avoid being blocked
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    news_items = self._parse_rss(response.text)
                    all_news.extend(news_items)
                else:
                    print(f"[NewsService] Error fetching {url}: Status {response.status_code}")
            except Exception as e:
                print(f"[NewsService] Failed to fetch {url}: {e}")

        # Sort by date (newest first) if possible, or just shuffle/merge
        # Since RSS parsing might vary, we assume the parsing order is "somewhat" chronological per feed.
        # Ideally we parse dates, but for MVP we just interleave or concat.
        
        # Deduplicate by title
        seen_titles = set()
        unique_news = []
        for item in all_news:
            if item['title'] not in seen_titles:
                unique_news.append(item)
                seen_titles.add(item['title'])

        # Update cache
        with self._lock:
            self.cached_headlines = unique_news
            self.last_fetch_time = datetime.now()
            print(f"[NewsService] Refreshed cache. Total items: {len(self.cached_headlines)}")
        
        return unique_news[:limit]

    def _parse_rss(self, xml_content):
        items = []
        try:
            root = ET.fromstring(xml_content)
            # Handle standard RSS 2.0
            channel = root.find('channel')
            if channel is not None:
                for item in channel.findall('item'):
                    title = item.find('title')
                    link = item.find('link')
                    pubDate = item.find('pubDate')
                    
                    if title is not None:
                        items.append({
                            'title': title.text,
                            'link': link.text if link is not None else '',
                            'pubDate': pubDate.text if pubDate is not None else ''
                        })
        except Exception as e:
            print(f"[NewsService] XML Parse Error: {e}")
        
        return items

# Singleton instance for easy import
news_service = NewsService()
