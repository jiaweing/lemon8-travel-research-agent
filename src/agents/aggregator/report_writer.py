"""Report file operations module."""

import os
from datetime import datetime
from src.utils.logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger('ReportWriter')

class ReportWriter:
    """Handles report file operations."""

    def __init__(self, output_dir: str):
        """Initialize the report writer.

        Args:
            output_dir (str): Base output directory
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"📁 Initialized report writer with output_dir: {output_dir}")

    def write_report(self, content: str, query: str) -> str:
        """Write final report to file.

        Args:
            content (str): Report content to write
            query (str): Search query for filename

        Returns:
            str: Path to written report file
        """
        try:
            # Generate report path
            report_path = self._get_report_path(query)
            
            # Write content
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            logger.info(f"✅ Report saved to: {report_path}")
            return report_path

        except Exception as e:
            error_msg = f"❌ Failed to write report: {str(e)}"
            logger.error(error_msg)
            raise

    def _get_report_path(self, query: str) -> str:
        """Generate path for report file.

        Args:
            query (str): Search query to use in filename

        Returns:
            str: Report file path
        """
        # Sanitize query for filename
        safe_query = self._sanitize_filename(query)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self.output_dir, f"{safe_query}_{timestamp}.md")

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Clean filename for safe file system use.

        Args:
            filename (str): Original filename

        Returns:
            str: Sanitized filename
        """
        # Remove invalid characters but preserve meaningful ones
        safe_chars = set(" -_()[]")
        cleaned = "".join(c if c.isalnum() or c in safe_chars else "_" for c in filename)
        
        # Clean up multiple underscores/spaces
        while "__" in cleaned:
            cleaned = cleaned.replace("__", "_")
        while "  " in cleaned:
            cleaned = cleaned.replace("  ", " ")
            
        # Trim and enforce length limit
        cleaned = cleaned.strip(" _")
        if len(cleaned) > 100:
            cleaned = cleaned[:100].rsplit(" ", 1)[0].strip()
            
        # Ensure we have a valid filename
        if not cleaned:
            cleaned = "report"
            
        return cleaned

    def append_to_report(self, report_path: str, content: str) -> None:
        """Append content to existing report.

        Args:
            report_path (str): Path to report file
            content (str): Content to append
        """
        try:
            with open(report_path, "a", encoding="utf-8") as f:
                f.write(f"\n\n{content}")
            logger.debug(f"✅ Content appended to: {report_path}")

        except Exception as e:
            logger.error(f"❌ Failed to append to report: {str(e)}")
            raise
