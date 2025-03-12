"""Content formatting utilities for the Lemon8 scraper."""

from typing import Dict, Optional
from bs4 import BeautifulSoup

def extract_page_title(html: str) -> str:
    """
    Extract page title from HTML content.
    
    Args:
        html (str): Raw HTML content
        
    Returns:
        str: Page title or empty string if not found
    """
    try:
        soup = BeautifulSoup(html, "html.parser")
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            return title_tag.string.strip()
    except Exception:
        pass
    return ""

def format_markdown_content(
    content: str,
    metadata: Dict[str, str],
    screenshot_path: Optional[str] = None,
) -> str:
    """
    Format markdown content with metadata and screenshot.
    
    Args:
        content (str): Raw markdown content
        metadata (Dict[str, str]): Metadata key-value pairs
        screenshot_path (Optional[str]): Path to screenshot file
        
    Returns:
        str: Formatted markdown with metadata header and screenshot
    """
    # Build metadata header
    header = ["---"]
    for key, value in metadata.items():
        header.append(f"{key}: {value}")
    if screenshot_path:
        # Ensure forward slashes in relative paths
        screenshot_path = screenshot_path.replace("\\", "/")
        header.append(f"screenshot: {screenshot_path}")
    header.extend(["---", ""])

    # Build content sections
    sections = []
    
    # Add screenshot if available
    if screenshot_path:
        screenshot_path = screenshot_path.replace("\\", "/")
        sections.append(f"![Post Screenshot]({screenshot_path})")
    
    # Add title if available
    if "title" in metadata:
        sections.append(f"# {metadata['title']}")
    
    # Add main content
    sections.append(content)

    # Combine all sections
    return "\n\n".join([
        "\n".join(header),
        "\n".join(sections)
    ])

def trim_irrelevant_sections(content: str) -> str:
    """
    Remove irrelevant sections from content.
    
    Args:
        content (str): Markdown content to clean
        
    Returns:
        str: Content with irrelevant sections removed
    """
    # List of section markers that indicate content to remove
    trim_markers = [
        "# Related posts",
        "# Related topics",
        "# You might also like",
        "# More from this creator"
    ]
    
    # Find first occurrence of any marker and trim content
    content = content.strip()
    for marker in trim_markers:
        if marker in content:
            content = content[:content.index(marker)].strip()
            
    return content
