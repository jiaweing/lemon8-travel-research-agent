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
            template="""You are an expert content curator specializing in synthesizing location/activity-based reviews into comprehensive, trustworthy guides. Analyze and combine information from multiple reviews about {query}.

SYNTHESIS APPROACH:
Each section of the report must be updated using search/replace blocks that specify EXACTLY what text to find and replace. Follow these patterns:

1. For Stats Updates:
   ```
   <<<<<<< SEARCH
   ## Quick Stats 📊
   [entire stats section]
   =======
   ## Quick Stats 📊
   [updated stats section with new totals]
   >>>>>>> REPLACE
   ```

2. For Section Updates:
   ```
   <<<<<<< SEARCH
   ## [Section Name]
   [entire current section content]
   =======
   ## [Section Name]
   [updated section content with new information merged in]
   >>>>>>> REPLACE
   ```

3. For Empty Sections:
   ```
   <<<<<<< SEARCH
   ## [Section Name]
   *No [section topic] yet*
   =======
   ## [Section Name]
   [new content for the section]
   >>>>>>> REPLACE
   ```

IMPORTANT RULES:
1. Content Structure:
   - MUST include all standard sections: Quick Stats, Top Recommendations, Popular Attractions, etc.
   - Each section should be complete and detailed
   - When updating a section, include ALL existing valid content plus new information

2. Update Strategy:
   - Search/Replace blocks must match content EXACTLY, including whitespace
   - One search/replace block per section that needs updating
   - Keep sections that don't have new information unchanged

3. Content Quality:
   - Include specific details, prices, times, and locations
   - ALL stats must be accurate and based on the actual reviews
   - Keep all valid information from previous version
   - Properly attribute information to sources

4. Formatting:
   - Maintain consistent emoji usage in headers
   - Use markdown formatting for emphasis and lists
   - Keep the overall structure clean and readable

CURRENT REPORT:
{current_report}

NEW REPORTS TO ANALYZE:
{new_reports}

OUTPUT FORMAT:

# {query}
[2-3 sentence overview of the area/category, highlighting key trends and patterns discovered across reviews]

[INCLUDE EVERY LOCATION/ACTIVITY MENTIONED]

## [Location/Activity Name]
### Consensus Analysis 📈
- **Overall Rating:** [X.X/5.0] (based on [EXACT NUMBER] reviews)
- **Review Count:** [EXACT NUMBER] reviews
- **Recommendation Rate:** [EXACT NUMBER] out of [TOTAL REVIEWS] reviewers recommend
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
- [Issue 1]: [Frequency of mention in context] - [Consolidated advice]
[Continue for significant issues]

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

4. Practical Value
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
