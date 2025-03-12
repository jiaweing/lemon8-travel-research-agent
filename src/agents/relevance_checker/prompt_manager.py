"""Manages LLM prompts for relevance checking."""

from langchain.prompts import PromptTemplate
from src.utils.logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger('PromptManager')

class RelevancePromptManager:
    """Manages prompts for relevance checking."""

    def __init__(self):
        """Initialize the prompt manager."""
        logger.info("📝 Initializing RelevancePromptManager")
        self._prompt_template = self._create_prompt_template()

    def _create_prompt_template(self) -> PromptTemplate:
        """Create the relevance evaluation prompt template.

        Returns:
            PromptTemplate: Configured prompt template
        """
        return PromptTemplate(
            input_variables=["content", "query"],
            template="""Evaluate if this content provides valuable information for the query: "{query}"

CONTENT:
{content}

CRITICAL VALIDATION:
1. First extract primary location(s) mentioned in the content
2. Check if those locations match or relate to the query location
3. Verify the content has actual meaningful information about those locations
4. REJECT content that:
   - Only mentions query location in metadata/UI
   - Has no specific location details/tips/recommendations
   - Is about a completely different location

Evaluate:
1. Relevance (0-1): How well does this content match the query intent?
2. Value: What makes this content useful for the query?
3. Gaps: What key aspects of the query does it not address?

RETURN A TUPLE OF THREE VALUES:

(
bool (is_relevant),  # True if overall score > 0.6
float (score),      # Relevance score between 0-1
str (reason)        # Explanation of value/gaps
)

FORMAT:
(True/False, 0.XX, "Explanation")

Examples of good explanations:
- "Provides detailed first-hand experience of [topic] (score: 0.85)"
- "Limited coverage of [topic], mostly focuses on unrelated aspects (score: 0.35)"
- "Comprehensive guide about [topic] with specific details (score: 0.95)"
"""
        )

    def format_prompt(self, content: str, query: str) -> str:
        """Format a prompt with content and query.

        Args:
            content (str): Content to evaluate
            query (str): Query to check relevance against

        Returns:
            str: Formatted prompt
        """
        return self._prompt_template.format(
            content=content,
            query=query
        )

    @property
    def template(self) -> PromptTemplate:
        """Get the prompt template.

        Returns:
            PromptTemplate: Current prompt template
        """
        return self._prompt_template
