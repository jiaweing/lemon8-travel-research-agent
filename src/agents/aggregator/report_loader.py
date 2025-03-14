"""Report loading and batching module."""

import os
from typing import Dict, Optional, List
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

    def load_latest_report(self) -> Optional[Dict[str, str]]:
        """Load the most recent report.

        Returns:
            Optional[Dict[str, str]]: Most recent report data or None if no reports exist
        """
        logger.info(f"📂 Loading latest report from {self.posts_dir}")
        try:
            # Get list of report files sorted by modification time (newest first)
            files = [(f, os.path.getmtime(os.path.join(self.posts_dir, f))) 
                    for f in os.listdir(self.posts_dir) if f.endswith('.md')]
            
            if not files:
                logger.info("No reports found")
                return None
                
            # Get the most recently modified file
            latest_file = max(files, key=lambda x: x[1])[0]
            report = self._load_single_report(latest_file)
            
            if report:
                logger.info(f"📄 Loaded latest report: {latest_file}")
                return report
            return None
            
        except Exception as e:
            error_msg = f"❌ Failed to load latest report: {str(e)}"
            logger.error(error_msg)
            return None

    def load_all_reports(self) -> List[Dict[str, str]]:
        """Load all available reports.

        Returns:
            List[Dict[str, str]]: List of all report data
        """
        logger.info(f"📂 Loading all reports from {self.posts_dir}")
        try:
            # Get list of all report files
            files = [f for f in os.listdir(self.posts_dir) if f.endswith('.md')]
            
            if not files:
                logger.info("No reports found")
                return []
            
            reports = []
            for filename in files:
                report = self._load_single_report(filename)
                if report:
                    reports.append(report)
                    
            logger.info(f"📄 Loaded {len(reports)} reports")
            return reports
            
        except Exception as e:
            error_msg = f"❌ Failed to load reports: {str(e)}"
            logger.error(error_msg)
            raise

    def _load_single_report(self, filename: str) -> Optional[Dict[str, str]]:
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
                    'filename': filepath
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
