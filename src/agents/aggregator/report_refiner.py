"""Report refinement and synthesis module."""

from typing import List, Dict
from datetime import datetime
from langchain_openai import ChatOpenAI
from crewai import Agent
from config import Config
from src.utils.logging_config import setup_logging, get_logger
from .prompt_manager import AggregationPromptManager

# Setup logging
setup_logging()
logger = get_logger('ReportRefiner')

class ReportRefiner:
    """Handles iterative report refinement and synthesis."""

    def __init__(self):
        """Initialize the report refiner."""
        logger.info("🤖 Initializing ReportRefiner")
        
        self.agent = Agent(
            role='Content Aggregator',
            goal='Create comprehensive summaries from multiple content sources',
            backstory="""You are an expert content aggregator that analyzes multiple reports
            to create detailed summaries. You identify patterns in recommendations,
            cross-validate information, and create ranked suggestions based on authentic sources."""
        )

        self.prompt_manager = AggregationPromptManager()
        self.llm = ChatOpenAI(
            model_name=Config.MODEL_NAME,
            temperature=0.3,  # Lower temperature for more consistent outputs
        )

    def _join_batch_content(self, batch: List[Dict[str, str]]) -> str:
        """Join batch reports into a single string.

        Args:
            batch (List[Dict[str, str]]): Batch of reports

        Returns:
            str: Combined report content
        """
        return "\n\n---\n\n".join(
            f"Report {i+1}:\n{report['content']}"
            for i, report in enumerate(batch)
        )

    async def refine_report(
        self,
        query: str,
        current_report: str,
        batch: List[Dict[str, str]]
    ) -> str:
        """Refine current report with new batch of reports.

        Args:
            query (str): Search query
            current_report (str): Current aggregated report
            batch (List[Dict[str, str]]): New batch of reports to analyze

        Returns:
            str: Refined report content
        """
        try:
            logger.debug(f"🔄 Refining report with batch of {len(batch)} reports")
            
            # Join batch content
            batch_content = self._join_batch_content(batch)
            
            # Format prompt
            prompt = self.prompt_manager.format_prompt(
                current_report=current_report,
                new_reports=batch_content,
                query=query
            )
            
            # Get refined content
            response = self.llm.invoke(prompt)
            
            if not hasattr(response, 'content'):
                logger.error("❌ No content in LLM response")
                return current_report
            
            logger.debug("✅ Report refinement complete")
            return response.content

        except Exception as e:
            error_msg = f"❌ Report refinement failed: {str(e)}"
            logger.error(error_msg)
            return current_report

    def get_initial_report(self, query: str) -> str:
        """Get initial report template.

        Args:
            query (str): Search query

        Returns:
            str: Initial report template
        """
        return f"""# {query}

Discover the best experiences this destination has to offer, backed by authentic reviews and local insights.

## Quick Stats 📊
- **Total Places Listed:** 0
- **Reviews Analyzed:** 0
- **Average Rating:** N/A
- **Price Range:** N/A

## Top Recommendations
*No recommendations yet - analyzing first review*

## Popular Attractions 🏛️
*No attractions analyzed yet*

## Dining and Food Scene 🍽️
*No dining information yet*

## Cultural Experiences 🎭
*No cultural experiences analyzed yet*

## Shopping and Markets 🛍️
*No shopping information yet*

## Transportation Tips 🚇
*No transportation tips yet*

## Accommodation Guide 🏨
*No accommodation information yet*

## Best Photo Spots 📸
*No photo spots analyzed yet*

## Safety and Tips 💡
*No safety information yet*

## Hidden Gems 💎
*No hidden gems discovered yet*

## Seasonal Highlights 🌸
*No seasonal information yet*

## Budget Planning 💰
*No budget information yet*

---

### Destination Insights
- **Best Time to Visit:** *Analyzing...*
- **Average Visit Duration:** *Analyzing...*
- **Language Tips:** *Analyzing...*
- **Local Customs:** *Analyzing...*

---
Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
