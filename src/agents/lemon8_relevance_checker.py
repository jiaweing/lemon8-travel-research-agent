"""Main relevance checker agent module."""

from typing import Tuple
from src.utils.logging_config import setup_logging, get_logger
from .relevance_checker.evaluator import RelevanceEvaluator

# Setup logging
setup_logging()
logger = get_logger('RelevanceCheckerAgent')

class Lemon8RelevanceCheckerAgent:
    """Main agent for checking content relevance."""

    def __init__(self):
        """Initialize the relevance checker agent."""
        logger.info("🤖 Initializing Lemon8RelevanceCheckerAgent")
        self.evaluator = RelevanceEvaluator()

    async def check_relevance(
        self,
        content_path: str,
        query: str,
        threshold: float = 0.6
    ) -> Tuple[bool, float, str]:
        """Check if content is relevant to the query.
        
        Args:
            content_path (str): Path to content file
            query (str): Search query to check relevance against
            threshold (float, optional): Minimum relevance score (0-1). Defaults to 0.6.
            
        Returns:
            Tuple[bool, float, str]: (meets_threshold, score, reason)
        """
        try:
            logger.info(f"🔍 Checking relevance for '{content_path}' against query: {query}")
            
            # Delegate to evaluator
            result = await self.evaluator.evaluate_content(
                content_path=content_path,
                query=query,
                threshold=threshold
            )
            
            logger.info("✅ Relevance check complete")
            return result
            
        except Exception as e:
            error_msg = f"❌ Relevance check failed: {str(e)}"
            logger.error(error_msg)
            return False, 0.0, error_msg
