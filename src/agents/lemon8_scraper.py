"""
Lemon8 Content Scraper

A scraper that finds and saves Lemon8 post content using crawl4ai.
Focuses on finding post URLs in a feed and saving each post's markdown content.

Example usage:
    scraper = Lemon8ScraperAgent()
    
    # Find posts from search
    posts = await scraper.scrape_search_results("best cafes in singapore")
    
    # Scrape individual post
    result = await scraper.scrape_post("https://www.lemon8-app.com/@user/123")
"""

import os
import hashlib
import base64
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import quote, urljoin
from PIL import Image
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig
from src.utils.logging_config import setup_logging, get_logger
from config import Config

# Set up logging with emojis for better visibility
setup_logging()
logger = get_logger('Lemon8Scraper')

class Lemon8ScraperAgent:
    """
    Agent for scraping content from Lemon8.
    
    Uses crawl4ai for reliable browser automation and BeautifulSoup for HTML parsing.
    Saves markdown content and 16:9 screenshots of posts to disk.
    
    Attributes:
        metadata_dir (str): Directory where scraped content is saved
        crawler (AsyncWebCrawler): Configured crawl4ai instance for web scraping
    """
    def _load_post_content(self, url: str) -> Optional[Dict[str, str]]:
        """
        Load markdown content and screenshot for a previously scraped post.
        
        Args:
            url (str): URL of the post to load
            
        Returns:
            Optional[Dict[str, str]]: Post data with URL, content path, and screenshot path if found,
                                    None if content hasn't been scraped yet
        """
        if not url:
            logger.warning("⚠️ Cannot load content: No URL provided")
            return None
            
        post_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]
        content_path = f"{self.metadata_dir}/{post_hash}.md"
        screenshot_path = f"{self.metadata_dir}/{post_hash}.png"
        
        if os.path.exists(content_path):
            logger.debug(f"📄 Found cached content for {url}")
            result = {'url': url, 'content_path': content_path}
            if os.path.exists(screenshot_path):
                result['screenshot_path'] = screenshot_path
            return result
        
        logger.debug(f"❓ No cached content found for {url}")    
        return None

    def __init__(self, run_id: str = None) -> None:
        """
        Initialize the Lemon8 scraper agent.
        
        Args:
            run_id (str, optional): Unique identifier for this scrape run.
                                  If None, generates based on datetime.
        """
        self.run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        # Use forward slashes for paths
        self.output_dir = f"{Config.OUTPUT_DIR}/{self.run_id}"
        self.metadata_dir = f"{self.output_dir}/metadata"
        self.seen_urls = set()  # Track URLs we've already processed
        
        browser_config = BrowserConfig(
            headless=Config.HEADLESS,
            viewport_width=1920,
            viewport_height=1080,
            user_agent=Config.USER_AGENT,
            extra_args=[
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--allow-running-insecure-content',
                '--disable-site-isolation-trials'
            ],
            headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'DNT': '1'
            }
        )
        self.crawler = AsyncWebCrawler(
            config=browser_config, 
            timeout=Config.TIMEOUT,
            use_stealth_js=True
        )
        
        # Create output directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)
        logger.info("🤖 Initialized Lemon8ScraperAgent")

    def _extract_posts_from_html(self, html: str, is_post_page: bool = False) -> List[str]:
        """
        Extract Lemon8 post URLs from HTML content.
        
        Finds links matching the Lemon8 post pattern and converts them to absolute URLs.
        When is_post_page=True, also looks for related/recommended posts.
        
        Args:
            html (str): Raw HTML content to parse
            is_post_page (bool): Whether this is a post page (to look for related posts)
            
        Returns:
            List[str]: List of unique Lemon8 post URLs found in the HTML
        """
        soup = BeautifulSoup(html, 'html.parser')
        posts = []
        
        # Find all links in the page
        # Use a more efficient CSS selector to find potential post links
        for link in soup.find_all('a', href=True):
            url = link['href']
            
            # Handle relative URLs by joining with base URL
            if not url.startswith('http'):
                url = urljoin('https://www.lemon8-app.com', url)
                
            # Match Lemon8 post URLs that:
            # 1. Start with http/https
            # 2. Have a username (@something)
            # 3. Have a numeric post ID
            # 4. Aren't profile or search pages
            # Parse URL path to extract parts
            path_parts = url.split('lemon8-app.com/')[-1].split('/')
            # A valid post URL should have format: @username/postid[?region=xx]
            if (
                url and 
                (url.startswith('http://') or url.startswith('https://')) and
                'lemon8-app.com' in url and
                len(path_parts) >= 2 and  # Must have at least @username and postid parts
                path_parts[0].startswith('@') and  # First part must be @username
                path_parts[1].split('?')[0].isdigit()  # Second part (before ?) must be numeric post ID
            ):
                logger.debug(f"🔗 Found post URL: {url}")
                posts.append(url)
                
        # If this is a post page, we've already found all valid post URLs above
        # No need for special handling - the same link detection logic works for recommendations
        if is_post_page:
            logger.info(f"🔗 Found {len(posts)} recommendation links in post page")
                        
        return list(set(posts))  # Remove duplicates

    async def scrape_search_results(self, query: str, max_posts: int = 5) -> List[str]:
        """
        Scrape Lemon8 search results for a given query.
        
        Gets the HTML content of a search results page and extracts post URLs.
        
        Args:
            query (str): Search query to find posts for
            max_posts (int): Maximum number of posts to return
            
        Returns:
            List[str]: List of post URLs found in search results.
            Empty list if no results found or on error.
            
        Example:
            >>> posts = await scraper.scrape_search_results("photography tips")
            >>> print(f"Found {len(posts)} posts")
        """
        encoded_query = quote(query)
        url = f"https://www.lemon8-app.com/discover/{encoded_query}?pid=website_seo_from_sug"
        logger.info(f"🔎 Starting content scraping for query: {query}")

        async with self.crawler as crawler:
            try:
                # Log start of scraping
                logger.info(f"🔍 Searching for {max_posts} posts matching '{query}'")
                
                config = CrawlerRunConfig(
                    screenshot=False,
                    magic=True,
                    simulate_user=True,
                    override_navigator=True,
                    cache_mode=CacheMode.BYPASS,
                    page_timeout=30000,
                    delay_before_return_html=5.0,  # Initial page load delay
                    js_code=f"""
                        new Promise(resolve => {{
                            const sleep = ms => new Promise(r => setTimeout(r, ms));
                            
                            // Function to scroll page and wait for content
                            const scrollPage = async () => {{
                                let lastHeight = 0;
                                let unchanged = 0;
                                const maxUnchanged = 3;

                                // Keep scrolling until height stops changing
                                while (unchanged < maxUnchanged) {{
                                    window.scrollTo(0, document.body.scrollHeight);
                                    await sleep(1000);

                                    const currentHeight = document.body.scrollHeight;
                                    console.log('Scroll height:', currentHeight);

                                    if (currentHeight === lastHeight) {{
                                        unchanged++;
                                    }} else {{
                                        unchanged = 0;
                                    }}
                                    lastHeight = currentHeight;

                                    // Also check network activity
                                    const entries = window.performance.getEntriesByType('resource');
                                    const recentEntries = entries.filter(e => 
                                        Date.now() - e.startTime < 2000 &&
                                        e.initiatorType !== 'script'
                                    );
                                    console.log('Recent network requests:', recentEntries.length);
                                    if (recentEntries.length > 0) {{
                                        unchanged = 0; // Reset if still loading
                                    }}
                                }}

                                window.scrollTo(0, 0);
                                await sleep(1000);
                            }};
                            
                            const clickSeeMore = async () => {{
                                // First try to find all shadow roots
                                function getAllShadowRoots(root) {{
                                    const shadows = [];
                                    function walk(node) {{
                                        const shadow = node.shadowRoot;
                                        if (shadow) shadows.push(shadow);
                                        const children = node.children;
                                        if (children) {{
                                            for (const child of children) {{
                                                walk(child);
                                            }}
                                        }}
                                    }}
                                    walk(root);
                                    return shadows;
                                }}

                                // Get all potential elements from both main DOM and shadow DOMs
                                const getAllElements = () => {{
                                    const elements = [];
                                    // Check main DOM
                                    document.querySelectorAll('*').forEach(el => {{
                                        if (el.textContent && el.textContent.toLowerCase().includes('see more')) {{
                                            elements.push(el);
                                        }}
                                    }});
                                    // Check shadow DOMs
                                    getAllShadowRoots(document.body).forEach(shadow => {{
                                        shadow.querySelectorAll('*').forEach(el => {{
                                            if (el.textContent && el.textContent.toLowerCase().includes('see more')) {{
                                                elements.push(el);
                                            }}
                                        }});
                                    }});
                                    return elements;
                                }};

                                // Find the most likely button among candidates
                                // Use XPath to find button-like elements containing "see more"
                                // Function to check if element or its children contain text
                                const hasText = (el, text) => {{
                                    if (el.nodeType === Node.TEXT_NODE) {{
                                        return el.textContent.toLowerCase().includes(text);
                                    }}
                                    for (const child of el.childNodes) {{
                                        if (hasText(child, text)) return true;
                                    }}
                                    return false;
                                }};

                                // Function to find clickable parent
                                const findClickableParent = (el) => {{
                                    let current = el;
                                    while (current && current !== document.body) {{
                                        const style = window.getComputedStyle(current);
                                        if (current.tagName === 'BUTTON' ||
                                            current.tagName === 'A' ||
                                            current.role === 'button' ||
                                            current.onclick ||
                                            style.cursor === 'pointer') {{
                                            return current;
                                        }}
                                        current = current.parentElement;
                                    }}
                                    return null;
                                }};

                                // Find all elements containing "see more" text
                                const treeWalker = document.createTreeWalker(
                                    document.body,
                                    NodeFilter.SHOW_TEXT,
                                    {{
                                        acceptNode: node => {{
                                            return node.textContent.toLowerCase().includes('see more') ?
                                                NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
                                        }}
                                    }}
                                );

                                const buttons = new Set();
                                while (treeWalker.nextNode()) {{
                                    const textNode = treeWalker.currentNode;
                                    const element = textNode.parentElement;
                                    const clickable = findClickableParent(element);
                                    
                                    if (clickable && 
                                        clickable.offsetParent && 
                                        window.getComputedStyle(clickable).display !== 'none') {{
                                        buttons.add(clickable);
                                    }}
                                }}

                                // Convert Set to Array and sort by position
                                const buttonArray = Array.from(buttons);
                                const button = buttonArray.sort((a, b) => {{
                                    const aRect = a.getBoundingClientRect();
                                    const bRect = b.getBoundingClientRect();
                                    return bRect.top - aRect.top;
                                }})[0];
                                
                                console.log('Found buttons:', buttons.length, 'Button details:', button?.outerHTML);
                                if (button) {{
                                    const prevHeight = document.documentElement.scrollHeight;
                                    button.click();
                                    
                                    // Wait for new content (max 2 seconds)
                                    for (let i = 0; i < 20; i++) {{
                                        await sleep(100);
                                        if (document.documentElement.scrollHeight > prevHeight) {{
                                            break;
                                        }}
                                    }}
                                    return true;
                                }}
                                return false;
                            }};
                            
                            (async () => {{
                                // Initial scroll to load content
                                await scrollPage();
                                // Get the target number of posts
                                const targetPosts = {max_posts};
                                let oldPostCount = 0;
                                let retryCount = 0;
                                const maxRetries = 3;  // Stop if no new posts after 3 clicks

                                // Keep clicking until we have enough posts or can't find more
                                while (true) {{
                                    // Find all post links (looking in both href and data attributes)
                                    const postLinks = new Set();
                                    document.querySelectorAll('a').forEach(a => {{
                                        const href = a.href || '';
                                        // Check URL pattern: /@username/numbers
                                        if (href.includes('/@') && RegExp('@[^/]+/[0-9]{5,}').test(href)) {{
                                            postLinks.add(href);
                                        }}
                                        // Also check data attributes that might contain the URL
                                        for (const attr of a.attributes) {{
                                            if (attr.name.startsWith('data-') && 
                                                attr.value.includes('/@') && 
                                                RegExp('@[^/]+/[0-9]{5,}').test(attr.value)) {{
                                                postLinks.add(attr.value);
                                            }}
                                        }}
                                    }});
                                    const currentPosts = postLinks.size;
                                    console.log('📊 Found posts:', currentPosts, 'New links:', Array.from(postLinks).slice(-5));
                                    
                                    // Stop if we have enough posts
                                    if (currentPosts >= targetPosts) break;
                                    
                                    // Stop if no new posts after several clicks
                                    if (currentPosts === oldPostCount) {{
                                        retryCount++;
                                        if (retryCount >= maxRetries) break;
                                    }} else {{
                                        retryCount = 0;
                                    }}
                                    
                                    oldPostCount = currentPosts;
                                    const clicked = await clickSeeMore();
                                    if (!clicked) break;  // Stop if no more "See more" button
                                    await sleep(1000);  // Wait between clicks
                                }}
                                
                                window.scrollTo(0, 0);
                                await sleep(1000);
                                resolve();
                            }})();
                        }})
                    """,
                )

                # Scrape search results page
                result = await crawler.arun(url=url, config=config)
                
                # Extract post URLs
                post_urls = self._extract_posts_from_html(result.html)
                
                post_count = len(post_urls)
                logger.info(f"✅ Found {post_count} posts for query: {query}")
                
                # Get double the requested posts since some might be irrelevant
                target_posts = max_posts * 2
                if post_count < target_posts:
                    logger.warning(f"⚠️ Only found {post_count} posts, trying to get {target_posts}")
                # Return more posts than requested to account for irrelevant ones
                return post_urls[:target_posts]

            except Exception as e:
                logger.error(f"❌ Error scraping search results: {str(e)}")
                return []

    def _is_valid_post_url(self, url: str) -> bool:
        """
        Check if a URL is a valid Lemon8 post URL.
        
        Args:
            url (str): URL to validate
            
        Returns:
            bool: True if URL is a valid post URL, False otherwise
        """
        try:
            path_parts = url.split('lemon8-app.com/')[-1].split('/')
            return (
                len(path_parts) >= 2 and  # Must have at least @username and postid parts
                path_parts[0].startswith('@') and  # First part must be @username
                path_parts[1].split('?')[0].isdigit()  # Second part (before ?) must be numeric post ID
            )
        except Exception:
            return False

    async def scrape_post(self, post_url: str, max_related: int = 5) -> Dict[str, str]:
        """
        Scrape content from a Lemon8 post URL using crawl4ai.
        
        Gets the markdown content and a screenshot of the post.
        Uses crawl4ai's magic=True mode which automatically converts content to markdown.
        Crops screenshots to 16:9 ratio for consistency.
        Also scrapes up to max_related related posts.
        
        Args:
            post_url (str): URL of the Lemon8 post to scrape
            max_related (int): Maximum number of related posts to scrape
            
        Returns:
            Dict[str, str]: Post data including:
                - url: Original post URL
                - content_path: Path where markdown content was saved
                - screenshot_path: Path where screenshot was saved (if successful)
                - related_posts: List of related post URLs found
            Empty dict if scraping failed
            
        Example:
            >>> result = await scraper.scrape_post("https://www.lemon8-app.com/@user/123")
            >>> print(f"Content saved to {result['content_path']}")
        """
        # Validate post URL first
        if not self._is_valid_post_url(post_url):
            logger.error(f"❌ Invalid post URL format: {post_url}")
            return {}
            
        if post_url in self.seen_urls:
            logger.info(f"⏩ Already scraped post: {post_url}")
            return {}
            
        logger.info(f"📥 Scraping post content: {post_url}")
        
        async with self.crawler as crawler:
            try:
                config = CrawlerRunConfig(
                    screenshot=True,  # Enable screenshots
                    screenshot_wait_for=3.0,  # Wait for content to load
                    magic=True,  # Enable markdown conversion
                    simulate_user=True,
                    override_navigator=True,
                    cache_mode=CacheMode.BYPASS,
                    page_timeout=30000,
                    delay_before_return_html=2.0,
                    js_code="""
                        new Promise(resolve => {
                            const sleep = ms => new Promise(r => setTimeout(r, ms));
                            
                            (async () => {
                                // Function to scroll page and wait for content
                                const scrollPage = async () => {
                                    let lastHeight = 0;
                                    let unchanged = 0;
                                    const maxUnchanged = 3;
                                    
                                    // Keep scrolling until height stops changing
                                    while (unchanged < maxUnchanged) {
                                        window.scrollTo(0, document.body.scrollHeight);
                                        await sleep(1000);
                                        
                                        const currentHeight = document.body.scrollHeight;
                                        console.log('Scroll height:', currentHeight);
                                        
                                        if (currentHeight === lastHeight) {
                                            unchanged++;
                                        } else {
                                            unchanged = 0;
                                        }
                                        lastHeight = currentHeight;
                                    }
                                    
                                    // Scroll back to top
                                    window.scrollTo(0, 0);
                                    await sleep(1000);
                                };
                                
                                // Scroll through the entire page to load all content including recommendations
                                await scrollPage();
                                
                                // Look for "More from this creator" or similar sections
                                console.log('Looking for recommendation sections...');
                                const recommendationTexts = [
                                    'more from', 'recommended', 'related', 'you might like', 
                                    'similar posts', 'also like', 'more posts'
                                ];
                                
                                // Find all text nodes in the document
                                const textNodes = [];
                                const walker = document.createTreeWalker(
                                    document.body, 
                                    NodeFilter.SHOW_TEXT, 
                                    null, 
                                    false
                                );
                                
                                while (walker.nextNode()) {
                                    const node = walker.currentNode;
                                    if (node.textContent.trim()) {
                                        textNodes.push(node);
                                    }
                                }
                                
                                // Check for recommendation sections
                                for (const node of textNodes) {
                                    const text = node.textContent.toLowerCase();
                                    if (recommendationTexts.some(rt => text.includes(rt))) {
                                        console.log('Found potential recommendation section:', text);
                                        // Scroll to this section to ensure content loads
                                        try {
                                            node.parentElement.scrollIntoView();
                                            await sleep(1000);
                                        } catch (e) {
                                            console.error('Error scrolling to recommendation section:', e);
                                        }
                                    }
                                }
                                
                                // Final scroll to top for screenshot
                                window.scrollTo(0, 0);
                                await sleep(1000);
                                
                                resolve();
                            })();
                        })
                    """
                )

                result = await crawler.arun(url=post_url, config=config)
                
                # Generate unique filename using first 16 chars of URL hash
                post_hash = hashlib.sha256(post_url.encode('utf-8')).hexdigest()[:16]
                content_path = f"{self.metadata_dir}/{post_hash}.md"
                
                # Process and save screenshot if available
                screenshot_path = None
                if result.screenshot:
                    screenshot_path = f"{self.metadata_dir}/{post_hash}.png"
                    screenshot_bytes = (
                        base64.b64decode(result.screenshot) 
                        if isinstance(result.screenshot, str)
                        else result.screenshot
                    )
                    
                    # Save original screenshot temporarily
                    temp_path = f"{self.metadata_dir}/{post_hash}_temp.png"
                    with open(temp_path, 'wb') as f:
                        f.write(screenshot_bytes)
                    
                    # Process with PIL for 16:9 ratio
                    with Image.open(temp_path) as img:
                        # Calculate dimensions for 16:9 aspect ratio
                        target_width = 1920
                        target_height = 1080
                        
                        # Calculate resize ratio to match target width
                        ratio = target_width / img.width
                        new_height = int(img.height * ratio)
                        
                        # Resize to target width
                        img = img.resize((target_width, new_height), Image.Resampling.LANCZOS)
                        
                        # Crop top portion to target height if needed
                        if new_height > target_height:
                            img = img.crop((0, 0, target_width, target_height))
                        
                        img.save(screenshot_path, 'PNG', optimize=True)
                    
                    # Clean up temp file
                    os.remove(temp_path)
                    logger.debug(f"📸 Screenshot saved as {target_width}x{target_height} PNG")
                else:
                    logger.warning("⚠️ No screenshot available for this post")
                
                # Save markdown content
                try:
                    # Add screenshot path to content if available
                    content = result.markdown.raw_markdown
                    
                    # Extract page title from HTML
                    page_title = ""
                    try:
                        soup = BeautifulSoup(result.html, 'html.parser')
                        title_tag = soup.find('title')
                        if title_tag and title_tag.string:
                            page_title = title_tag.string.strip()
                            logger.info(f"📄 Extracted page title: {page_title}")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to extract page title: {str(e)}")
                        
                    # Add metadata header with citation, title, screenshot info
                    metadata = [
                        "---",
                        f"source: {post_url}",
                    ]
                    if page_title:
                        metadata.append(f"title: {page_title}")
                    if screenshot_path:
                        # Ensure forward slashes in relative paths
                        relative_screenshot_path = os.path.relpath(screenshot_path, self.metadata_dir).replace('\\', '/')
                        metadata.append(f"screenshot: {relative_screenshot_path}")
                    metadata.append("---\n\n")

                    # Start content with screenshot and page title
                    content_start = []
                    if screenshot_path:
                        # Ensure forward slashes in relative paths
                        relative_screenshot_path = os.path.relpath(screenshot_path, self.metadata_dir).replace('\\', '/')
                        content_start.append(f"![Post Screenshot]({relative_screenshot_path})")
                    if page_title:
                        content_start.append(f"# {page_title}")
                    content_start.append("")  # Add blank line
                    
                    content = "\n".join(metadata) + content

                    with open(content_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f"✅ Successfully scraped and saved post: {post_url}")
                    logger.debug(f"📁 Content saved to: {content_path}")
                except IOError as e:
                    logger.error(f"💾 Failed to save content for {post_url}: {str(e)}")
                    return {}

                # Extract related posts from the page
                related_posts = self._extract_posts_from_html(result.html, is_post_page=True)
                related_posts = related_posts[:max_related]
                
                # Mark as scraped
                self.seen_urls.add(post_url)
                
                return {
                    'url': post_url, 
                    'content_path': content_path,
                    'screenshot_path': screenshot_path,
                    'related_posts': related_posts
                }

            except Exception as e:
                logger.error(f"❌ Error scraping post {post_url}")
                logger.error(f"🔍 Details: {str(e)}")
                return {}
