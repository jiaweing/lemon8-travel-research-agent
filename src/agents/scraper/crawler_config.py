"""Crawler configuration for the Lemon8 scraper."""

import os
from dataclasses import dataclass
from typing import Dict
from crawl4ai import CrawlerRunConfig, CacheMode, BrowserConfig
from .utils.js_utils import read_js_from_file

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
    TIMEOUT: int = 30000  # 30 seconds
    
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
    def get_config(max_posts: int = 5) -> CrawlerRunConfig:
        """Get crawler config for search pages."""
        js_dir = os.path.join(os.path.dirname(__file__), "js")
        
        return CrawlerRunConfig(
            screenshot=False,
            magic=True,
            simulate_user=True,
            override_navigator=True,
            cache_mode=CacheMode.BYPASS,
            page_timeout=30000,
            delay_before_return_html=5.0,
            js_code=_build_search_js(
                js_dir=js_dir,
                max_posts=max_posts
            )
        )

class PostConfig:
    """Configuration for individual post crawling."""
    
    @staticmethod
    def get_config() -> CrawlerRunConfig:
        """Get crawler config for post pages."""
        js_dir = os.path.join(os.path.dirname(__file__), "js")
        
        return CrawlerRunConfig(
            screenshot=True,
            screenshot_wait_for=3.0,
            magic=True,
            simulate_user=True,
            override_navigator=True,
            cache_mode=CacheMode.BYPASS,
            page_timeout=30000,
            delay_before_return_html=2.0,
            js_code=_build_post_js(js_dir)
        )

def _build_search_js(js_dir: str, max_posts: int) -> str:
    """Build JavaScript code for search page crawling."""
    scroll_utils = read_js_from_file(os.path.join(js_dir, "scroll_utils.js"))
    content_loader = read_js_from_file(os.path.join(js_dir, "content_loader.js"))
    
    return f"""
        {scroll_utils}
        {content_loader}
        
        new Promise(resolve => {{
            (async () => {{
                // Initial scroll to load content
                await scrollPage();
                
                // Get the target number of posts
                const targetPosts = {max_posts};
                let oldPostCount = 0;
                let retryCount = 0;
                const maxRetries = 3;  // Stop if no new posts after 3 clicks
                
                while (true) {{
                    // Find all post links
                    const postLinks = new Set();
                    document.querySelectorAll('a').forEach(a => {{
                        const href = a.href || '';
                        // Check URL pattern: /@username/numbers
                        if (href.includes('/@') && RegExp('@[^/]+/[0-9]{{5,}}').test(href)) {{
                            postLinks.add(href);
                        }}
                        
                        // Also check data attributes
                        for (const attr of a.attributes) {{
                            if (attr.name.startsWith('data-') && 
                                attr.value.includes('/@') && 
                                RegExp('@[^/]+/[0-9]{{5,}}').test(attr.value)) {{
                                postLinks.add(attr.value);
                            }}
                        }}
                    }});
                    
                    const currentPosts = postLinks.size;
                    console.log(
                        '📊 Found posts:', currentPosts,
                        'New links:', Array.from(postLinks).slice(-5)
                    );
                    
                    if (currentPosts >= targetPosts) break;
                    
                    if (currentPosts === oldPostCount) {{
                        retryCount++;
                        if (retryCount >= maxRetries) break;
                    }} else {{
                        retryCount = 0;
                    }}
                    
                    oldPostCount = currentPosts;
                    const clicked = await clickSeeMore();
                    if (!clicked) break;
                    await sleep(1000);
                }}
                
                window.scrollTo(0, 0);
                await sleep(1000);
                resolve();
            }})();
        }})
    """

def _build_post_js(js_dir: str) -> str:
    """Build JavaScript code for post page crawling."""
    scroll_utils = read_js_from_file(os.path.join(js_dir, "scroll_utils.js"))
    
    return f"""
        {scroll_utils}
        
        new Promise(resolve => {{
            (async () => {{
                // Initial scroll to load content
                await scrollPage();
                
                // Look for recommendation sections
                console.log('Looking for recommendation sections...');
                const recommendationTexts = [
                    'more from', 'recommended', 'related',
                    'you might like', 'similar posts',
                    'also like', 'more posts'
                ];
                
                const textNodes = [];
                const walker = document.createTreeWalker(
                    document.body,
                    NodeFilter.SHOW_TEXT,
                    null,
                    false
                );
                
                while (walker.nextNode()) {{
                    const node = walker.currentNode;
                    if (node.textContent.trim()) {{
                        textNodes.push(node);
                    }}
                }}
                
                // Find and scroll to recommendation sections
                for (const node of textNodes) {{
                    const text = node.textContent.toLowerCase();
                    if (recommendationTexts.some(rt => text.includes(rt))) {{
                        console.log('Found recommendation section:', text);
                        try {{
                            node.parentElement.scrollIntoView();
                            await sleep(1000);
                        }} catch (e) {{
                            console.error(
                                'Error scrolling to recommendation section:',
                                e
                            );
                        }}
                    }}
                }}
                
                // Final scroll to top for screenshot
                window.scrollTo(0, 0);
                await sleep(1000);
                
                resolve();
            }})();
        }})
    """
