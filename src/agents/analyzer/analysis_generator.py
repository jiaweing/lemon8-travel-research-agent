"""LLM-based content analysis generation module."""

from typing import Optional
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from crewai import Agent
from src.config import Config
from src.utils.logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger('AnalysisGenerator')

class AnalysisGenerator:
    """Handles LLM-based content analysis generation."""

    def __init__(self):
        """Initialize the analysis generator with LLM and agent."""
        logger.info("🤖 Initializing AnalysisGenerator")
        
        self.agent = Agent(
            role='Content Analyzer',
            goal='Analyze content and extract structured information',
            backstory="""You are an expert content analyzer that processes posts 
            to extract key information, insights and recommendations."""
        )
        
        self.llm = ChatOpenAI(
            model_name=Config.MODEL_NAME,
            temperature=0.2,  # Lower temperature for consistent analysis
        )

        self._prompt_template = self._create_prompt_template()

    def _create_prompt_template(self) -> PromptTemplate:
        """Create the analysis prompt template.

        Returns:
            PromptTemplate: Configured prompt template
        """
        return PromptTemplate(
            input_variables=["content", "source_url"],
            template="""=========================================
INPUT CONTENT:
=========================================
{content}

=========================================
SOURCE URL:
=========================================
{source_url}

=========================================
ANALYSIS INSTRUCTIONS:
=========================================

You are a professional content analyst specializing in location-based reviews and recommendations. Your task is to analyze content and extract valuable insights in a structured, engaging format.

MANDATORY LOCATION VALIDATION - READ THIS FIRST:
1. Extract the post title and find any explicit location mention.
   Examples: "Things to do in LONDON", "TOKYO food guide", "Best cafes in PARIS"
   
2. This explicitly mentioned location in the title becomes your PRIMARY LOCATION.
   - If title says "LONDON", you MUST analyze as a London post
   - If title says "TOKYO", you MUST analyze as a Tokyo post
   - NO EXCEPTIONS

3. URL parameters like ?region=sg, usernames, profile locations etc. MUST BE COMPLETELY IGNORED.
   They have NOTHING to do with the post content location.

4. If you find yourself writing about a location different from what's in the title:
   - STOP IMMEDIATELY
   - DELETE everything
   - Start over focusing on the location from the title

CRITICAL: Re-read the title before starting. Extract the location. Lock that location in your mind.

CRITICAL CONTENT FILTERING:
1. ONLY analyze content between the post title and any "Related posts" section
2. COMPLETELY IGNORE:
   - All URLs and their parameters
   - Website navigation/UI text
   - Related posts sections
   - "You may also like" sections
   - Comments section
   - Footer/header content
   - Social sharing buttons
   - App store links
   - Region indicators from UI/URLs

INPUT RULES:
- FIRST: Identify and stick to ONLY the locations from the main post content
- SECOND: Determine the appropriate currency and terminology for those specific locations
- Process all content before any "Related posts" section
- Preserve all tiktokcdn.com image URLs in their original format
- Extract key metrics (likes, saves, comments, followers) for the overview
- Only describe locations/activities that are explicitly mentioned in the original content
- Note price points, operational hours, and practical details directly from the content
- Pay attention to author's personal experiences and recommendations

CRITICAL: If you notice your analysis drifting to a different location than what's in the original content, STOP and realign to the correct location. Every recommendation must be backed by the original content.

=========================================
OUTPUT FORMAT:
=========================================

# Overview
[Write a compelling 2-3 sentence summary that captures the essence of the post and its unique value proposition]

_Source: {source_url}_

### Engagement Analysis 📊
- **Community Response:** [X] Likes • [X] Saves • [X] Comments
- **Creator Impact:** [X] Followers • [Brief note on creator's authority in this topic]
- **Content Quality:** [High/Medium/Low - based on detail level, image quality, usefulness]

### Featured Locations/Activities 🗺
[List all locations/activities mentioned in the content, with brief value propositions]
- [Name]: [What makes it special/worth visiting]

---

[REQUIRED: Create a detailed section for EACH location/activity mentioned in the content]

## [Location/Activity Name]
![Representative Image](best_quality_image_url)

**Essential Info:**
- 📍 Location: [Detailed address + Alternative names if applicable]
- ⏰ Hours: [Operating hours + Best timing recommendations]
- 💰 Price Range: [Cost breakdown in appropriate local currency + Value assessment]
- ⌛ Duration: [Recommended visit length + Peak hours warning if relevant]
- 🎯 Best For: [Ideal visitor profile/occasion]

### What Makes It Special ✨
[3-4 compelling sentences about unique selling points]
[Include standout features that differentiate it]
[Mention any signature items/experiences]

### Visitor Experience 🎟
- **Atmosphere:** [Description of ambiance, crowd, setting]
- **Service:** [Notable service aspects]
- **Facilities:** [Available amenities, accessibility]
- **Unique Features:** [Special offerings or characteristics]

### Pro Tips 💡
[4-5 actionable tips in bullet points]
- 🎯 [Reservation tips/timing strategies]
- 🎯 [Must-try items/experiences]
- 🎯 [Money-saving hacks]
- 🎯 [Common pitfalls to avoid]

### Visual Highlights 📸
[Include 2-3 most impactful images with descriptive captions]
![Detail Shot](detail_image_url)
[Caption explaining what's shown and why it's noteworthy]

---"""
        )

    async def generate_analysis(self, content: str, source_url: Optional[str] = None) -> str:
        """Generate analysis for the given content.

        Args:
            content (str): Content to analyze
            source_url (Optional[str], optional): Source URL. Defaults to None.

        Returns:
            str: Generated analysis text
        """
        try:
            logger.debug("🔍 Starting content analysis")
            logger.debug(f"Content length: {len(content)} characters")
            
            # Format prompt with content and source URL
            formatted_prompt = self._prompt_template.format(
                content=content,
                source_url=source_url or "[Source URL not available]"
            )

            # Generate analysis using LLM
            response = self.llm.invoke(formatted_prompt)
            
            if not hasattr(response, 'content'):
                raise ValueError("No content in LLM response")

            logger.info("✅ Analysis generation complete")
            return response.content

        except Exception as e:
            error_msg = f"❌ Analysis generation failed: {str(e)}"
            logger.error(error_msg)
            raise
