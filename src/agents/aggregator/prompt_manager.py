"""Prompt management for report aggregation."""

from langchain.prompts import PromptTemplate
from src.utils.logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger('AggregationPromptManager')

class AggregationPromptManager:
    """Manages prompts for report aggregation."""

    def __init__(self):
        """Initialize the prompt manager."""
        logger.info("📝 Initializing AggregationPromptManager")
        self._prompt_template = self._create_prompt_template()

    def _create_prompt_template(self) -> PromptTemplate:
        """Create the report refinement prompt template.

        Returns:
            PromptTemplate: Configured prompt template
        """
        return PromptTemplate(
            input_variables=["current_report", "new_reports", "query"],
            template="""You are an expert content curator specializing in synthesizing location-based reviews into comprehensive, trustworthy guides. Analyze and combine information from multiple reviews about {query}.

SYNTHESIS APPROACH:
1. Cross-validate information across reviews
2. Weight recent reviews more heavily
3. Identify patterns in experiences and recommendations
4. Aggregate pricing data with dates for accuracy
5. Consolidate practical tips and warnings
6. Preserve unique insights while focusing on consensus

CURRENT REPORT:
{current_report}

NEW REPORTS TO ANALYZE:
{new_reports}

OUTPUT FORMAT:

# {query} - Curated Guide
[2-3 sentence overview of the area/category, highlighting key trends and patterns discovered across reviews]

## Quick Stats 📊
- **Total Places Reviewed:** [Number]
- **Review Period:** [Earliest] to [Latest]
- **Aggregate Reviews:** [Total number of unique reviews analyzed]
- **Price Range:** [Min]-[Max] SGD across all venues
- **Most Reviewed Areas:** [List top 3 neighborhoods/districts]

## Top Recommendations 🏆
[List of top 3-5 most consistently praised places, sorted by review frequency and rating]
1. [Name] - [One-line value proposition] - [X/Y reviews recommend]
2. [Continue format]

---

[FOR EVERY LOCATION MENTIONED, NOT JUST IN THE TOP RECOMMENDATIONS, DO THE FOLLOWING]

## [Location Name]
![Best Available Image](highest_quality_image_url)

### Consensus Analysis 📈
- **Overall Rating:** [X.X/5.0] (Weighted average from [Y] reviews)
- **Recommendation Rate:** [X] out of [Y] reviewers recommend
- **Price Consistency:** [High/Medium/Low] (noting price variations)
- **Experience Rating:** [% positive experiences]
- **Reviewer Agreement:** [Strong/Moderate/Mixed] on key aspects

**Review Sources:** [List all Lemon8 URLs chronologically with dates]

### Validated Information ✓
- 📍 **Location:** [Cross-referenced address & landmarks]
- ⏰ **Hours:** [Confirmed operating hours + Notable variations]
- 💰 **Current Pricing:** [Price range with recent dates]
  - [Specific menu items/services with consistent pricing]
  - [Note any price trends or variations]
- ⌛ **Visit Planning:** [Consolidated timing recommendations]
  - Peak Hours: [Consensus on busy times]
  - Recommended Duration: [Average from reports]

### Key Highlights ✨
[3-4 most consistently mentioned positive aspects]
- [Feature]: [Number of mentions] - [Synthesized description]
![Supporting Image](relevant_image_url)
[Additional validated highlights with evidence]

### Visitor Experience 🎭
- **Atmosphere:** [Consensus description with any notable variations]
- **Service Quality:** [Pattern in service experiences]
- **Crowd Profile:** [Typical visitor demographics/timing]
- **Accessibility:** [Validated transport/parking info]

### Essential Tips 💡
[Consistently mentioned advice across reviews]
- 🎯 Best Times: [Synthesized from multiple experiences]
- 🎯 Reservations: [Combined booking guidance]
- 🎯 Must-Try Items: [Most recommended items across reviews]
- 🎯 Value Tips: [Aggregated money-saving advice]

### Watch Out For ⚠️
[Common challenges or concerns mentioned across reviews]
- [Issue 1]: [Frequency of mention] - [Consolidated advice]
[Continue for significant issues]

### Photo Evidence 📸
[Include 2-3 best images that validate key points]
![Detail Image](detail_image_url)
[Caption explaining significance and source]

---

QUALITY CONTROL CHECKLIST:
1. Information Currency
   - Prioritize recent reviews
   - Note dates for price/operational info
   - Flag outdated information

2. Validation Standards
   - Include only multi-source verified facts
   - Note significant discrepancies
   - Indicate confidence levels

3. Bias Prevention
   - Balance positive and critical reviews
   - Note sponsored/promotional content
   - Consider reviewer expertise

4. Visual Documentation
   - Use recent, relevant images
   - Preserve image quality
   - Caption with context

5. Practical Value
   - Focus on actionable information
   - Include specific prices and times
   - Provide clear recommendations"""
        )

    def format_prompt(
        self,
        current_report: str,
        new_reports: str,
        query: str
    ) -> str:
        """Format a prompt with current and new reports.

        Args:
            current_report (str): Current aggregated report
            new_reports (str): New reports to analyze
            query (str): Search query

        Returns:
            str: Formatted prompt
        """
        return self._prompt_template.format(
            current_report=current_report,
            new_reports=new_reports,
            query=query
        )

    @property
    def template(self) -> PromptTemplate:
        """Get the prompt template.

        Returns:
            PromptTemplate: Current prompt template
        """
        return self._prompt_template
