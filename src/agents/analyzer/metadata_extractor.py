"""Metadata extraction and processing module."""

import os
from typing import Dict
from src.utils.logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger('MetadataExtractor')

class MetadataExtractor:
    """Handles metadata extraction from content and info files."""

    @staticmethod
    def extract_metadata(content: str, content_path: str) -> Dict[str, str]:
        """Extract metadata from both content frontmatter and info file.

        Args:
            content (str): Raw content with potential frontmatter
            content_path (str): Path to content file (for finding info file)

        Returns:
            Dict[str, str]: Combined metadata from both sources
        """
        metadata = {}

        try:
            # Extract from frontmatter
            if content.startswith('---'):
                end_idx = content.find('\n---', 3)
                if end_idx != -1:
                    frontmatter = content[3:end_idx]
                    MetadataExtractor._parse_metadata(frontmatter, metadata)

            # Extract from info file
            content_hash = os.path.basename(content_path).split('_')[0]
            info_path = os.path.join(os.path.dirname(content_path), f"{content_hash}_info.txt")
            
            if os.path.exists(info_path):
                with open(info_path, 'r', encoding='utf-8') as f:
                    MetadataExtractor._parse_metadata(f.read(), metadata)

            logger.debug(f"📋 Extracted metadata keys: {list(metadata.keys())}")
            return metadata

        except Exception as e:
            logger.error(f"❌ Metadata extraction failed: {str(e)}")
            return {}

    @staticmethod
    def _parse_metadata(content: str, metadata: Dict[str, str]) -> None:
        """Parse key-value pairs from text into metadata dict.

        Args:
            content (str): Text to parse
            metadata (Dict[str, str]): Dictionary to update with parsed values
        """
        for line in content.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip()

    @staticmethod
    def parse_title(metadata: Dict[str, str]) -> str:
        """Parse title from metadata, handling various formats.

        Args:
            metadata (Dict[str, str]): Metadata dictionary

        Returns:
            str: Processed title
        """
        try:
            raw_title = (
                metadata.get('title') or  # From frontmatter
                metadata.get('Title') or  # From info file
                'Untitled Post'  # Default
            )

            title_parts = raw_title.split(' | ')
            if len(title_parts) >= 3:
                post_title = title_parts[0]
                author = title_parts[1].replace('Gallery posted by ', '')
                return f"{post_title} by {author}"
            
            return raw_title

        except Exception as e:
            logger.error(f"❌ Title parsing failed: {str(e)}")
            return "Untitled Post"

    @staticmethod
    def clean_title_for_filename(title: str) -> str:
        """Clean title for use in filenames while preserving meaning.

        Args:
            title (str): Title to clean

        Returns:
            str: Filename-safe title
        """
        try:
            # Remove invalid characters but preserve spaces and meaningful punctuation
            safe_chars = set(" -_()[]{}'")
            cleaned = "".join(c if c.isalnum() or c in safe_chars else "_" for c in title)
            
            # Clean up multiple underscores/spaces
            while "__" in cleaned:
                cleaned = cleaned.replace("__", "_")
            while "  " in cleaned:
                cleaned = cleaned.replace("  ", " ")
                
            cleaned = cleaned.strip(" _")
            
            if not cleaned:
                return "untitled"
                
            if len(cleaned) > 100:
                words = cleaned[:100].rsplit(' ', 1)[0]
                cleaned = words.strip(" _")
                
            return cleaned

        except Exception as e:
            logger.error(f"❌ Title cleaning failed: {str(e)}")
            return "untitled"
