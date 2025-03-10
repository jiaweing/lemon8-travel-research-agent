"""
Lemon8 Scraper Configuration

Loads and validates environment variables for the scraper.
Creates required directories and provides configuration defaults.

Environment Variables:
    HEADLESS (bool): Run browser in headless mode (default: true)
    TIMEOUT (int): Browser timeout in seconds (default: 30)
    HTTP_PROXY (str): HTTP proxy URL (optional)
    HTTPS_PROXY (str): HTTPS proxy URL (optional)
    USER_AGENT (str): Browser user agent string (has default)
    CONTENT_DIR (str): Directory for scraped content (default: content)
    MAX_POSTS (int): Maximum posts to scrape per query (default: 50)
    SCROLL_DELAY (float): Delay between scroll operations (default: 1.0)
"""

import os
from typing import ClassVar
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Configuration settings for the Lemon8 scraper.
    
    All settings can be configured via environment variables.
    Provides defaults for optional settings.
    """
    
    # Browser settings
    HEADLESS: ClassVar[bool] = os.getenv('HEADLESS', 'true').lower() == 'true'
    TIMEOUT: ClassVar[int] = int(os.getenv('TIMEOUT', '30'))
    
    # Network settings
    HTTP_PROXY: ClassVar[str] = os.getenv('HTTP_PROXY', '')
    HTTPS_PROXY: ClassVar[str] = os.getenv('HTTPS_PROXY', '')
    USER_AGENT: ClassVar[str] = os.getenv('USER_AGENT', 
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    )
    
    # Output settings
    CONTENT_DIR: ClassVar[str] = os.getenv('CONTENT_DIR', 'content')
    
    # Scraping settings
    MAX_POSTS: ClassVar[int] = int(os.getenv('MAX_POSTS', '50'))
    SCROLL_DELAY: ClassVar[float] = float(os.getenv('SCROLL_DELAY', '1.0'))
    
    @classmethod
    def validate(cls) -> None:
        """
        Validate the configuration and create required directories.
        
        Creates the content directory if it doesn't exist.
        No validation errors are possible in the current configuration.
        
        Future validation rules can be added here as needed.
        """
        # Ensure content directory exists
        os.makedirs(cls.CONTENT_DIR, exist_ok=True)
