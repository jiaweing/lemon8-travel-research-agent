"""Main report aggregation agent module."""

from typing import Optional
from datetime import datetime
from src.utils.logging_config import setup_logging, get_logger
from .aggregator.report_loader import ReportLoader
from .aggregator.prompt_manager import AggregationPromptManager
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
        output_dir = f"output/{run_id}"
        
        self.report_loader = ReportLoader(output_dir)
        self.report_refiner = ReportRefiner()
        self.report_writer = ReportWriter(output_dir)

    async def generate_final_report(self, query: str) -> str:
        """Generate a final consolidated report.

        Args:
            query (str): Search query

        Returns:
            str: Path to final report file
        """
        try:
            logger.info(f"📊 Starting report generation for: {query}")
            
            # Load reports in batches
            report_batches = self.report_loader.load_reports()
            
            # Get initial report template
            current_report = self.report_refiner.get_initial_report(query)
            
            # Process each batch iteratively
            for i, batch in enumerate(report_batches, 1):
                logger.info(f"🔄 Processing batch {i} of {len(report_batches)}")
                
                # Refine report with new batch
                current_report = await self.report_refiner.refine_report(
                    query=query,
                    current_report=current_report,
                    batch=batch
                )
            
            # Write final report
            final_report_path = self.report_writer.write_report(
                content=current_report,
                query=query
            )
            
            logger.info(f"✅ Report completed at {final_report_path}")
            return final_report_path
            
        except Exception as e:
            error_msg = f"Report generation failed: {str(e)}"
            logger.error(error_msg)
            return error_msg
