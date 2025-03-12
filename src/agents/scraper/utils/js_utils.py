"""JavaScript utilities for the scraper."""

def read_js_from_file(filepath: str) -> str:
    """Read JavaScript code from a file.

    Args:
        filepath (str): Path to JavaScript file

    Returns:
        str: JavaScript code content
    
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file can't be read
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()
