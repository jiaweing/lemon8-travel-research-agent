"""Main analyzer agent module."""

import os
from typing import Optional
from datetime import datetime
from src.utils.logging_config import setup_logging, get_logger
from .analyzer.content_processor import ContentProcessor
from .analyzer.metadata_extractor import MetadataExtractor
from .analyzer.analysis_generator import AnalysisGenerator
from .analyzer.report_builder import ReportBuilder

# Setup logging
setup_logging()
logger = get_logger('AnalyzerAgent')

class Lemon8AnalyzerAgent:
    """Main analyzer agent that orchestrates content analysis."""

    def __init__(self, run_id: Optional[str] = None):
        """Initialize the analyzer agent.

        Args:
            run_id (Optional[str], optional): Run identifier. Defaults to timestamp.
        """
        logger.info("🤖 Initializing Lemon8AnalyzerAgent")
        
        # Initialize components
        run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.content_processor = ContentProcessor()
        self.metadata_extractor = MetadataExtractor()
        self.analysis_generator = AnalysisGenerator()
        self.report_builder = ReportBuilder(run_id)

    async def analyze_content(self, content_path: str) -> str:
        """Analyze content and generate a report.

        Args:
            content_path (str): Path to content file

        Returns:
            str: Path to generated report
        """
        try:
            logger.info(f"📊 Starting analysis for: {content_path}")

            # Read content
            with open(content_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract and process content
            frontmatter, main_content, sections = self.content_processor.extract_content_sections(content)
            clean_content = self.content_processor.clean_content(main_content)

            # Extract metadata and title
            metadata = self.metadata_extractor.extract_metadata(content, content_path)
            title = self.metadata_extractor.parse_title(metadata)
            source_url = metadata.get('source')

            # Generate analysis
            analysis = await self.analysis_generator.generate_analysis(clean_content, source_url)

            # Get screenshot path from metadata and ensure it exists
            screenshot_path = None
            if 'screenshot' in metadata:
                screenshot_path = os.path.join("..", metadata['screenshot'])
                # Normalize path to use forward slashes
                screenshot_path = screenshot_path.replace('\\', '/')
                if not os.path.exists(screenshot_path):
                    logger.warning(f"⚠️ Screenshot not found at {screenshot_path}")
                    screenshot_path = None
                else:
                    logger.debug(f"📸 Found screenshot at {screenshot_path}")

            # Build and save report
            content_preview = clean_content[:200] + "..." if len(clean_content) > 200 else clean_content
            report_path = self.report_builder.build_report(
                title=title,
                analysis=analysis,
                source_url=source_url,
                content_preview=content_preview,
                content_length=len(clean_content),
                screenshot_path=screenshot_path if os.path.exists(screenshot_path) else None
            )

            logger.info(f"✅ Analysis completed: {report_path}")
            return report_path

        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            logger.error(error_msg)
            return error_msg
