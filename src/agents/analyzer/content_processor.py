"""Content extraction and processing module."""

import re
import os
from typing import List, Tuple
from src.utils.logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger('ContentProcessor')

class ContentProcessor:
    """Handles content extraction and processing."""

    @staticmethod
    def extract_content_sections(content: str) -> Tuple[str, str, List[str]]:
        """Extract frontmatter, main content, and sections from raw content.

        Args:
            content (str): Raw content string

        Returns:
            Tuple[str, str, List[str]]: Frontmatter, main content, and sections
        """
        try:
            frontmatter = ""
            main_content = content
            
            # Extract frontmatter if present
            if content.startswith('---'):
                end_idx = content.find('\n---', 3)
                if end_idx != -1:
                    frontmatter = content[3:end_idx]
                    main_content = content[end_idx + 4:].strip()

            # Split into sections
            lines = main_content.split('\n')
            sections = []
            current_section = []

            for line in lines:
                if line.startswith('# ') and not line.startswith('## '):
                    if current_section:
                        sections.append('\n'.join(current_section))
                    current_section = [line]
                else:
                    current_section.append(line)

            if current_section:
                sections.append('\n'.join(current_section))

            logger.debug(f"📑 Extracted {len(sections)} content sections")
            return frontmatter, main_content, sections

        except Exception as e:
            logger.error(f"❌ Content extraction failed: {str(e)}")
            return "", content, [content]

    @staticmethod
    def clean_content(content: str) -> str:
        """Clean and normalize content text.

        Args:
            content (str): Raw content to clean

        Returns:
            str: Cleaned content
        """
        try:
            # Remove UI elements and navigation
            skip_patterns = [
                'lemon8-app.com',
                'Follow',
                'followers',
                'Open Lemon8',
                'See more',
                '1/',
                'You may also like',
                'Related posts',
                'See more comments',
                'See more on the app',
                '## Related',
                '## Comments'
            ]

            lines = content.split('\n')
            cleaned_lines = []
            
            for line in lines:
                if not any(pattern in line for pattern in skip_patterns):
                    cleaned_lines.append(line)

            content = '\n'.join(cleaned_lines)

            # Clean up markdown and formatting
            content = re.sub(r'\n{3,}', '\n\n', content)  # Multiple newlines
            content = re.sub(r'!\[.*?\]\(.*?\)', '', content)  # Image markdown
            content = re.sub(r'\[(?!#).*?\]\(.*?\)', '', content)  # Links except hashtags
            content = re.sub(r'\?region=[a-z]{2}', '', content)  # Region parameters
            content = re.sub(r'Open in (the )?Lemon8.*$', '', content, flags=re.MULTILINE)
            content = re.sub(r'@\w+\s+\|\s+\w+\s+follower.*$', '', content, flags=re.MULTILINE)

            logger.debug(f"📊 Cleaned content length: {len(content)} characters")
            return content.strip()

        except Exception as e:
            logger.error(f"❌ Content cleaning failed: {str(e)}")
            return content

    @staticmethod
    def extract_title(content: str) -> str:
        """Extract the main title from content.

        Args:
            content (str): Content to extract title from

        Returns:
            str: Extracted title or "Untitled"
        """
        try:
            lines = content.split('\n')
            for line in lines:
                if line.startswith('# ') and not line.startswith('## '):
                    return line.lstrip('# ').strip()
            return "Untitled"

        except Exception as e:
            logger.error(f"❌ Title extraction failed: {str(e)}")
            return "Untitled"
