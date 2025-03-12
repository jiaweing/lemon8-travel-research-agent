"""Response parsing and validation for relevance checking."""

from typing import Tuple
from src.utils.logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger('ResponseParser')

class ResponseParser:
    """Parses and validates LLM responses for relevance checking."""

    @staticmethod
    def parse_response(response_text: str) -> Tuple[bool, float, str]:
        """Parse LLM response into structured relevance data.

        Args:
            response_text (str): Raw response text from LLM

        Returns:
            Tuple[bool, float, str]: (is_relevant, score, reason)
        """
        try:
            # Clean the response text
            clean_response = response_text.strip('`() \n')
            
            # Split into parts
            parts = clean_response.split(',', 2)
            if len(parts) != 3:
                raise ValueError(f"Expected 3 parts, got {len(parts)}")
            
            # Parse is_relevant (bool)
            is_relevant = parts[0].strip().lower() == 'true'
            
            # Parse score (float)
            try:
                score = float(parts[1].strip())
                if not 0 <= score <= 1:
                    raise ValueError(f"Score {score} out of range [0,1]")
            except ValueError as e:
                logger.error(f"❌ Invalid score format: {parts[1]}")
                raise ValueError(f"Invalid score: {str(e)}")
            
            # Parse reason (str)
            reason = parts[2].strip().strip('"\'')
            if not reason:
                raise ValueError("Empty reason")
            
            logger.debug(f"✅ Parsed response: {is_relevant=}, {score=:.2f}")
            return is_relevant, score, reason
            
        except Exception as e:
            logger.error(f"❌ Failed to parse response: {str(e)}")
            logger.error(f"Response text was: {response_text}")
            return False, 0.0, f"Error parsing response: {str(e)}"

    @staticmethod
    def format_result(
        is_relevant: bool,
        score: float,
        reason: str,
        threshold: float
    ) -> Tuple[bool, float, str]:
        """Format results with threshold check.

        Args:
            is_relevant (bool): Raw relevance flag
            score (float): Relevance score
            reason (str): Explanation
            threshold (float): Minimum score threshold

        Returns:
            Tuple[bool, float, str]: (meets_threshold, score, reason)
        """
        meets_threshold = score >= threshold
        
        formatted_reason = (
            f"{reason} (score: {score:.2f}"
            + (f" ≥ {threshold:.2f})" if meets_threshold else f" < {threshold:.2f})")
        )
        
        logger.debug(f"📊 Formatted result: {meets_threshold=}, {score=:.2f}")
        return meets_threshold, score, formatted_reason
