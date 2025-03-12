"""URL handling utilities for the Lemon8 scraper."""

from urllib.parse import urljoin, quote
from typing import List


def is_valid_post_url(url: str) -> bool:
    """
    Check if a URL is a valid Lemon8 post URL.
    
    Args:
        url (str): URL to validate
            
    Returns:
        bool: True if URL is a valid post URL, False otherwise
    """
    try:
        path_parts = url.split("lemon8-app.com/")[-1].split("/")
        return (
            len(path_parts) >= 2 and  # Must have at least @username and postid parts
            path_parts[0].startswith("@") and  # First part must be @username
            path_parts[1].split("?")[0].isdigit()  # Second part (before ?) must be numeric post ID
        )
    except Exception:
        return False


def normalize_url(url: str) -> str:
    """
    Convert relative URLs to absolute URLs for Lemon8.
    
    Args:
        url (str): URL to normalize
        
    Returns:
        str: Absolute URL with lemon8-app.com domain
    """
    if not url.startswith("http"):
        return urljoin("https://www.lemon8-app.com", url)
    return url


def get_search_url(query: str) -> str:
    """
    Generate search URL for a query.
    
    Args:
        query (str): Search query
        
    Returns:
        str: Lemon8 search URL
    """
    encoded_query = quote(query)
    return f"https://www.lemon8-app.com/discover/{encoded_query}?pid=website_seo_from_sug"


def extract_post_urls(html: str) -> List[str]:
    """
    Extract Lemon8 post URLs from HTML content.
    
    Finds links matching the Lemon8 post pattern and converts them to absolute URLs.
    
    Args:
        html (str): Raw HTML content to parse
            
    Returns:
        List[str]: List of unique Lemon8 post URLs found in the HTML
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    posts = []

    for link in soup.find_all("a", href=True):
        url = normalize_url(link["href"])
        if is_valid_post_url(url):
            posts.append(url)

    return list(set(posts))
