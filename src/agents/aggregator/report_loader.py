"""Report loading and batching module."""

import os
from typing import List, Dict
from src.utils.logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger('ReportLoader')

class ReportLoader:
    """Handles loading and batching of reports."""

    def __init__(self, output_dir: str):
        """Initialize the report loader.

        Args:
            output_dir (str): Base output directory containing reports
        """
        self.output_dir = output_dir
        self.posts_dir = os.path.join(output_dir, "posts")
        
        # Ensure directories exist
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(self.posts_dir, exist_ok=True)
        
        logger.info(f"📁 Initialized report loader with output_dir: {output_dir}")

    def load_reports(self, batch_size: int = 5) -> List[List[Dict[str, str]]]:
        """Load reports in batches.

        Args:
            batch_size (int, optional): Number of reports per batch. Defaults to 5.

        Returns:
            List[List[Dict[str, str]]]: List of batches, each containing reports
        """
        logger.info(f"📂 Loading posts from {self.posts_dir}")
        try:
            all_reports = []
            batch = []
            
            # Load reports in sorted order
            for filename in sorted(os.listdir(self.posts_dir)):
                if filename.endswith('.md'):
                    report = self._load_single_report(filename)
                    if report:
                        batch.append(report)
                        
                    if len(batch) >= batch_size:
                        all_reports.append(batch)
                        batch = []
            
            # Add any remaining reports
            if batch:
                all_reports.append(batch)
                
            logger.info(f"📄 Loaded {sum(len(batch) for batch in all_reports)} reports in {len(all_reports)} batches")
            return all_reports

        except Exception as e:
            error_msg = f"❌ Failed to load reports: {str(e)}"
            logger.error(error_msg)
            raise

    def _load_single_report(self, filename: str) -> Dict[str, str]:
        """Load a single report file.

        Args:
            filename (str): Name of the report file

        Returns:
            Dict[str, str]: Report data or None if loading fails
        """
        try:
            filepath = os.path.join(self.posts_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                return {
                    'content': f.read(),
                    'filename': filename
                }

        except Exception as e:
            logger.error(f"❌ Failed to load report {filename}: {str(e)}")
            return None

    def get_report_path(self, query: str) -> str:
        """Generate path for final report.

        Args:
            query (str): Search query for report

        Returns:
            str: Final report file path
        """
        # Sanitize query for filename
        safe_query = "".join(c if c.isalnum() or c in " -_" else "_" for c in query)
        safe_query = safe_query.replace(" ", "_")[:100]
        return os.path.join(self.output_dir, f"{safe_query}.md")
