"""Core relevance evaluation logic."""

from typing import Tuple
from langchain_openai import ChatOpenAI
from src.config import Config
from src.utils.logging_config import setup_logging, get_logger
from .prompt_manager import RelevancePromptManager
from .response_parser import ResponseParser

# Setup logging
setup_logging()
logger = get_logger('RelevanceEvaluator')

class RelevanceEvaluator:
    """Handles content relevance evaluation."""

    def __init__(self):
        """Initialize the relevance evaluator."""
        logger.info("🤖 Initializing RelevanceEvaluator")
        
        # Initialize components
        self.prompt_manager = RelevancePromptManager()
        self.response_parser = ResponseParser()
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            temperature=0.2,  # Low temperature for consistent evaluations
        )

    def _clean_content(self, content: str) -> str:
        """Clean content for evaluation.

        Args:
            content (str): Raw content

        Returns:
            str: Cleaned content
        """
        # Trim content if it starts with Related posts/topics
        for marker in ["# Related posts", "# Related topics"]:
            if marker in content:
                content = content[:content.index(marker)].strip()
        return content

    async def evaluate_content(
        self,
        content_path: str,
        query: str,
        threshold: float = 0.6
    ) -> Tuple[bool, float, str]:
        """Evaluate content relevance against a query.

        Args:
            content_path (str): Path to content file
            query (str): Query to check relevance against
            threshold (float, optional): Minimum relevance score. Defaults to 0.6.

        Returns:
            Tuple[bool, float, str]: (meets_threshold, score, reason)
        """
        try:
            # Read and clean content
            with open(content_path, 'r', encoding='utf-8') as f:
                content = f.read()
            content = self._clean_content(content)
            
            # Debug logging
            logger.debug("🔍 EVALUATING CONTENT:")
            logger.debug("-" * 80)
            logger.debug(content[:500] + "..." if len(content) > 500 else content)
            logger.debug("-" * 80)
            logger.debug(f"🔎 QUERY: {query}")
            
            # Generate prompt and get LLM response
            prompt = self.prompt_manager.format_prompt(content, query)
            response = self.llm.invoke(prompt)
            
            if not hasattr(response, 'content'):
                raise ValueError("No content in LLM response")
            
            # Parse response
            is_relevant, score, reason = self.response_parser.parse_response(
                response.content
            )
            
            # Format final result
            result = self.response_parser.format_result(
                is_relevant=is_relevant,
                score=score,
                reason=reason,
                threshold=threshold
            )
            
            logger.info(f"✅ Evaluation complete: {score:.2f} - {reason}")
            return result

        except Exception as e:
            error_msg = f"❌ Evaluation failed: {str(e)}"
            logger.error(error_msg)
            return False, 0.0, error_msg
