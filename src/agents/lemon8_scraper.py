"""Lemon8 content scraper module."""

import os
import hashlib
from datetime import datetime
from typing import Dict, List, Optional

from crawl4ai import AsyncWebCrawler

from src.utils.logging_config import setup_logging, get_logger
from src.config import Config
from .scraper.crawler_config import CrawlerSettings, SearchConfig, PostConfig
from .scraper.utils.url_utils import (
    is_valid_post_url,
    get_search_url,
    extract_post_urls
)
from .scraper.utils.image_utils import process_screenshot
from .scraper.utils.content_utils import (
    extract_page_title,
    format_markdown_content,
    trim_irrelevant_sections
)

# Set up logging
setup_logging()
logger = get_logger("Lemon8Scraper")

class Lemon8ScraperAgent:
    """
    Agent for scraping content from Lemon8.
    
    Uses crawl4ai for browser automation and scraping. Handles:
    - Searching for posts by query
    - Scraping individual post content
    - Processing and saving screenshots
    - Formatting and saving markdown content
    
    Attributes:
        run_id (str): Unique identifier for this scrape run
        output_dir (str): Base directory for output files
        metadata_dir (str): Directory for markdown content and screenshots
        seen_urls (set): Set of URLs already processed
        crawler (AsyncWebCrawler): Configured web crawler instance
    """
    
    def __init__(self, run_id: str = None) -> None:
        """Initialize the scraper agent."""
        self.run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = f"{Config.OUTPUT_DIR}/{self.run_id}"
        self.metadata_dir = f"{self.output_dir}/metadata"
        self.seen_urls = set()
        
        # Create output directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)
        
        # Initialize crawler with base settings
        self.crawler = AsyncWebCrawler(
            config=CrawlerSettings.get_browser_config(),
            timeout=CrawlerSettings.TIMEOUT,
            use_stealth_js=True
        )
        
        logger.info("🤖 Initialized Lemon8ScraperAgent")
        
    def _get_content_paths(self, url: str) -> tuple[str, str]:
        """Get paths for content and screenshot files."""
        post_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
        return (
            f"{self.metadata_dir}/{post_hash}.md",
            f"{self.metadata_dir}/{post_hash}.png"
        )

    def _load_post_content(self, url: str) -> Optional[Dict[str, str]]:
        """Load previously scraped post content."""
        if not url:
            logger.warning("⚠️ Cannot load content: No URL provided")
            return None
        
        content_path, screenshot_path = self._get_content_paths(url)
        
        if os.path.exists(content_path):
            logger.debug(f"📄 Found cached content for {url}")
            result = {"url": url, "content_path": content_path}
            if os.path.exists(screenshot_path):
                result["screenshot_path"] = screenshot_path
            return result
            
        logger.debug(f"❓ No cached content found for {url}")
        return None

    async def scrape_search_results(
        self,
        query: str,
        max_posts: int = 5
    ) -> List[str]:
        """Scrape Lemon8 search results for a query."""
        url = get_search_url(query)
        logger.info(f"🔎 Starting content scraping for query: {query}")

        async with self.crawler as crawler:
            try:
                result = await crawler.arun(
                    url=url,
                    config=SearchConfig.get_config(max_posts)
                )
                
                # Extract post URLs
                post_urls = extract_post_urls(result.html)
                post_count = len(post_urls)
                
                logger.info(f"✅ Found {post_count} posts for query: {query}")
                return post_urls[:max_posts]

            except Exception as e:
                logger.error(f"❌ Error scraping search results: {str(e)}")
                return []

    async def scrape_post(
        self,
        post_url: str,
        max_related: int = 5
    ) -> Dict[str, str]:
        """Scrape content from a Lemon8 post URL."""
        if not is_valid_post_url(post_url):
            logger.error(f"❌ Invalid post URL format: {post_url}")
            return {}
            
        if post_url in self.seen_urls:
            logger.info(f"⏩ Already scraped post: {post_url}")
            return {}
            
        logger.info(f"📥 Scraping post content: {post_url}")
        
        async with self.crawler as crawler:
            try:
                # Get content paths
                content_path, screenshot_path = self._get_content_paths(post_url)
                
                # Scrape post page
                result = await crawler.arun(
                    url=post_url,
                    config=PostConfig.get_config()
                )
                
                # Process screenshot if available
                final_screenshot_path = None
                if result.screenshot:
                    final_screenshot_path = process_screenshot(
                        screenshot_data=result.screenshot,
                        output_path=screenshot_path
                    )
                    if final_screenshot_path:
                        logger.debug(f"📸 Screenshot saved to {final_screenshot_path}")
                    else:
                        logger.warning("⚠️ Failed to process screenshot")
                else:
                    logger.warning("⚠️ No screenshot available for this post")
                
                # Extract and format content
                try:
                    # Get page title and clean content
                    page_title = extract_page_title(result.html)
                    content = trim_irrelevant_sections(result.markdown.raw_markdown)
                    
                    # Format with metadata
                    metadata = {"source": post_url}
                    if page_title:
                        metadata["title"] = page_title
                        logger.info(f"📄 Extracted page title: {page_title}")
                    
                    # Get screenshot path relative to content file
                    if final_screenshot_path:
                        rel_screenshot_path = os.path.relpath(
                            final_screenshot_path,
                            self.metadata_dir
                        )
                    else:
                        rel_screenshot_path = None
                    
                    # Format and save content
                    formatted_content = format_markdown_content(
                        content=content,
                        metadata=metadata,
                        screenshot_path=rel_screenshot_path
                    )
                    
                    with open(content_path, "w", encoding="utf-8") as f:
                        f.write(formatted_content)
                        
                    logger.info(f"✅ Successfully scraped and saved post: {post_url}")
                    logger.debug(f"📁 Content saved to: {content_path}")
                    
                except IOError as e:
                    logger.error(f"💾 Failed to save content: {str(e)}")
                    return {}

                # Extract related posts
                related_posts = extract_post_urls(result.html)[:max_related]
                
                # Mark as scraped
                self.seen_urls.add(post_url)
                
                return {
                    "url": post_url,
                    "content_path": content_path,
                    "screenshot_path": final_screenshot_path,
                    "related_posts": related_posts
                }

            except Exception as e:
                logger.error(f"❌ Error scraping post {post_url}: {str(e)}")
                return {}
