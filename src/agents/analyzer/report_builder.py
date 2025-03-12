"""Report generation and formatting module."""

import os
from datetime import datetime
from typing import Optional
from src.utils.logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger('ReportBuilder')

class ReportBuilder:
    """Handles report generation and formatting."""

    def __init__(self, run_id: Optional[str] = None):
        """Initialize the report builder.

        Args:
            run_id (Optional[str], optional): Run identifier. Defaults to timestamp.
        """
        self.run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = os.path.join("output", self.run_id)
        self.metadata_dir = os.path.join(self.output_dir, "metadata")
        self.posts_dir = os.path.join(self.output_dir, "posts")

        # Create required directories
        os.makedirs(self.metadata_dir, exist_ok=True)
        os.makedirs(self.posts_dir, exist_ok=True)
        
        logger.info(f"📁 Initialized report builder with run_id: {self.run_id}")

    def build_report(
        self,
        title: str,
        analysis: str,
        source_url: Optional[str],
        content_preview: str,
        content_length: int,
        screenshot_path: Optional[str] = None
    ) -> str:
        """Build a formatted markdown report.

        Args:
            title (str): Report title
            analysis (str): Generated analysis content
            source_url (Optional[str]): Source URL of the content
            content_preview (str): Preview of the analyzed content
            content_length (int): Length of analyzed content
            screenshot_path (Optional[str], optional): Path to screenshot. Defaults to None.

        Returns:
            str: Path to the generated report file
        """
        try:
            # Format report content
            report = f"""# {title}

{f'![Screenshot]({screenshot_path})' if screenshot_path else ''}

{analysis}

---
Source: {source_url or '[Source URL not available]'}
Analyzed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Content Length: {content_length} characters
Content Preview: {content_preview}
"""
            # Generate safe filename
            safe_title = self.clean_title_for_filename(title)
            report_path = os.path.join(self.posts_dir, f"{safe_title}.md")

            # Save report
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)

            logger.info(f"✅ Report saved: {report_path}")
            return report_path

        except Exception as e:
            error_msg = f"❌ Report building failed: {str(e)}"
            logger.error(error_msg)
            raise

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

    @staticmethod
    def get_report_title(report_path: str) -> str:
        """Extract the title from a report file.

        Args:
            report_path (str): Path to the report file

        Returns:
            str: Extracted title or filename
        """
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Get first heading
                lines = content.split('\n')
                for line in lines:
                    if line.startswith('# '):
                        return line[2:].strip()
                return os.path.basename(report_path)

        except Exception as e:
            logger.error(f"❌ Failed to get report title: {str(e)}")
            return os.path.basename(report_path)
