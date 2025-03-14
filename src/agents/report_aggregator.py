"""Main report aggregation agent module."""

import os
from typing import Optional
from datetime import datetime
from src.utils.logging_config import setup_logging, get_logger
from .aggregator.report_loader import ReportLoader
from .aggregator.report_refiner import ReportRefiner
from .aggregator.report_writer import ReportWriter

# Setup logging
setup_logging()
logger = get_logger('ReportAggregator')

class ReportAggregatorAgent:
    """Main agent for aggregating and synthesizing reports."""

    def __init__(self, run_id: Optional[str] = None):
        """Initialize the report aggregator agent.

        Args:
            run_id (Optional[str], optional): Run identifier. Defaults to timestamp.
        """
        logger.info("🤖 Initializing ReportAggregatorAgent")
        
        # Initialize components
        run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = f"output/{run_id}"
        
        self.report_loader = ReportLoader(self.output_dir)
        self.report_refiner = ReportRefiner()
        self.report_writer = ReportWriter(self.output_dir)

    async def generate_final_report(self, query: str) -> str:
        """Generate a final consolidated report.

        Args:
            query (str): Search query

        Returns:
            str: Path to final report file
        """
        try:
            logger.info(f"📊 Starting report generation for: {query}")
            
            # Load latest report
            latest_report = self.report_loader.load_latest_report()
            
            # Get path for the final report
            report_name = f"{query.replace(' ', '_').lower()}.md"
            report_path = os.path.join(self.output_dir, report_name).replace('\\', '/')
            
            # Try to read existing report or create new one
            try:
                with open(report_path, 'r', encoding='utf-8') as f:
                    current_report = f.read()
            except FileNotFoundError:
                # First post or report doesn't exist yet
                current_report = self.report_refiner.get_initial_report(query)
                self.report_writer.write_report(
                    content=current_report,
                    query=query
                )
            
            if latest_report:
                # Process the latest report and update existing content
                refined_content = await self.report_refiner.refine_report(
                    query=query,
                    current_report=current_report,
                    batch=[latest_report]
                )
                
                # If refinement returned search/replace blocks, update the report
                if "<<<<<<< SEARCH" in refined_content:
                    success, errors = self.report_writer.update_report(report_path, refined_content)
                else:
                    # If no search/replace blocks, treat as full content replacement
                    logger.info("No search/replace blocks found, using full content update")
                    self.report_writer.write_report(
                        content=refined_content,
                        query=query
                    )
                    success = True
                    errors = []
                if not success:
                    logger.error(f"Failed to update report: {errors}")
                    return ""
                
                logger.info(f"✅ Updated report with new content")
            
            logger.info(f"✅ Report completed at {report_path}")
            return report_path
            
        except Exception as e:
            error_msg = f"Report generation failed: {str(e)}"
            logger.error(error_msg)
            return error_msg
