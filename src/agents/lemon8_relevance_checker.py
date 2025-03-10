from typing import List, Dict, Tuple, Optional
import os
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from src.utils.logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger('RelevanceChecker')

class Lemon8RelevanceCheckerAgent:
    def __init__(self):
        """Initialize the relevance checker agent"""
        logger.info("🤖 Initializing Lemon8RelevanceCheckerAgent")
        
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            temperature=0.3,  # Lower temperature for more consistent evaluations
        )
        
        self.relevance_prompt = PromptTemplate(
            input_variables=["content", "query"],
            template="""Evaluate if this content provides valuable information for the query: "{query}"

CONTENT:
{content}

Consider:
1. How directly does this content address the query?
2. What specific, relevant information does it provide?
3. Is the information based on firsthand experience or reliable sources?

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

    async def check_relevance(self, content_path: str, query: str, threshold: float = 0.6) -> Tuple[bool, float, str]:
        """
        Check if content is relevant to the query
        
        Args:
            content_path: Path to content file
            query: Search query to check relevance against
            threshold: Minimum relevance score (0-1)
            
        Returns:
            Tuple of (is_relevant, score, reason)
        """
        try:
            # Read content file
            with open(content_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Format prompt
            prompt = self.relevance_prompt.format(
                content=content,
                query=query
            )
            
            # Get evaluation
            response = self.llm.invoke(prompt)
            
            if not hasattr(response, 'content'):
                logger.error("❌ No content in response")
                return False, 0.0, "Failed to evaluate content"
            
            # Parse response - expected format: (True/False, 0.XX, "reason")
            try:
                # Remove any markdown formatting
                clean_response = response.content.strip('`() \n')
                
                # Split parts and handle formatting
                parts = clean_response.split(',', 2)
                
                is_relevant = parts[0].strip().lower() == 'true'
                score = float(parts[1].strip())
                reason = parts[2].strip().strip('"\'')
                
                logger.info(f"✅ Relevance check: {score:.2f} - {reason}")
                return bool(score >= threshold), score, reason
                
            except Exception as e:
                logger.error(f"❌ Failed to parse response: {str(e)}")
                logger.error(f"Response was: {response.content}")
                return False, 0.0, f"Error parsing response: {str(e)}"
            
        except Exception as e:
            logger.error(f"❌ Relevance check failed: {str(e)}")
            return False, 0.0, str(e)
