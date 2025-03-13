"""Crawler configuration for the Lemon8 scraper."""

import os
from dataclasses import dataclass
from crawl4ai import BestFirstCrawlingStrategy, CrawlerRunConfig, CacheMode, BrowserConfig, DomainFilter, FilterChain, KeywordRelevanceScorer, LXMLWebScrapingStrategy
from crawl4ai.deep_crawling import URLPatternFilter

@dataclass
class CrawlerSettings:
    """Base crawler settings that apply to all operations."""
    
    HEADLESS: bool = True
    VIEWPORT_WIDTH: int = 1920
    VIEWPORT_HEIGHT: int = 1080
    USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    )
    TIMEOUT: int = 60000  # 60 seconds for dynamic content
    
    @classmethod
    def get_browser_config(cls) -> BrowserConfig:
        """Get browser configuration."""
        return BrowserConfig(
            headless=cls.HEADLESS,
            viewport_width=cls.VIEWPORT_WIDTH,
            viewport_height=cls.VIEWPORT_HEIGHT,
            user_agent=cls.USER_AGENT,
            extra_args=[
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--allow-running-insecure-content",
                "--disable-site-isolation-trials"
            ],
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "DNT": "1"
            }
        )

class SearchConfig:
    """Configuration for search page crawling."""
    
    @staticmethod
    def get_config(query: str, max_posts: int = 5) -> CrawlerRunConfig:
        """Get crawler config for search pages."""
        
        return CrawlerRunConfig(
            deep_crawl_strategy=BestFirstCrawlingStrategy(
                max_depth=2,
                max_pages=max_posts * 10,
                include_external=False,
                filter_chain=FilterChain([
                    DomainFilter(allowed_domains=["www.lemon8-app.com"]),
                    URLPatternFilter(patterns=["@*/*", "discover/*"]),
                ]),
                url_scorer=KeywordRelevanceScorer(
                    keywords=query.split(),
                    weight=0.7
                )
            ),
            # scraping_strategy=LXMLWebScrapingStrategy(),
            screenshot=False,
            magic=True,
            simulate_user=True,
            override_navigator=True,
            cache_mode=CacheMode.BYPASS,
            page_timeout=60000,
            delay_before_return_html=10.0,
            js_code=_build_search_js(),
            stream=True,
            verbose=True
        )

class PostConfig:
    """Configuration for individual post crawling."""
    
    @staticmethod
    def get_config() -> CrawlerRunConfig:
        """Get crawler config for post pages."""
        
        return CrawlerRunConfig(
            screenshot=True,
            screenshot_wait_for=3.0,
            magic=True,
            simulate_user=True,
            override_navigator=True,
            cache_mode=CacheMode.BYPASS,
            page_timeout=60000,
            delay_before_return_html=5.0,
        )

def _build_search_js() -> str:
    """Build JavaScript code for search page crawling."""
    return """
        new Promise(resolve => {
            setTimeout(() => {
                window.scrollTo(0, 0);
                setTimeout(resolve, 500);
            }, 2000);
        })
    """