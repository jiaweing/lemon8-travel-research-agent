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
    OUTPUT_DIR (str): Directory for scraped content (default: output)
    SCROLL_DELAY (float): Delay between scroll operations (default: 1.0)
    MODEL_NAME (str): OpenAI model name to use (default: gpt-4o-mini)
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
    # LLM settings
    MODEL_NAME: ClassVar[str] = os.getenv('MODEL_NAME', 'gpt-4o-mini')
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
    OUTPUT_DIR: ClassVar[str] = os.getenv('OUTPUT_DIR', 'output')
    
    # Scraping settings
    SCROLL_DELAY: ClassVar[float] = float(os.getenv('SCROLL_DELAY', '1.0'))
    
    @classmethod
    def validate(cls) -> None:
        """
        Validate the configuration and create required directories.
        
        Creates the output directory if it doesn't exist.
        No validation errors are possible in the current configuration.
        
        Future validation rules can be added here as needed.
        """
        # Ensure content directory exists
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
