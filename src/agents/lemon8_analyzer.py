from typing import Dict, Optional
import os
from datetime import datetime
import re
from crewai import Agent
from src.config import Config
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from src.utils.logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger('ContentAnalyzer')

class Lemon8AnalyzerAgent:
    def __init__(self, run_id: str = None):
        """Initialize the content analyzer agent"""
        logger.info("🤖 Initializing Lemon8AnalyzerAgent")
        self.run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = os.path.join("output", self.run_id)
        self.metadata_dir = os.path.join(self.output_dir, "metadata")
        self.posts_dir = os.path.join(self.output_dir, "posts")
        # Create required directories
        os.makedirs(self.metadata_dir, exist_ok=True)
        os.makedirs(self.posts_dir, exist_ok=True)
        
        self.agent = Agent(
            role='Content Analyzer',
            goal='Analyze content and extract structured information',
            backstory="""You are an expert content analyzer that processes posts 
            to extract key information, insights and recommendations."""
        )
        self.llm = ChatOpenAI(
            model_name=Config.MODEL_NAME,
            temperature=0.2,  # Lower temperature for stricter adherence to instructions
        )

    def _extract_metadata(self, content: str, content_path: str) -> Dict[str, str]:
        """Extract metadata from both content frontmatter and info file"""
        metadata = {}

        try:
            # First try to get metadata from content frontmatter
            if content.startswith('---'):
                end_idx = content.find('\n---', 3)
                if end_idx != -1:
                    frontmatter = content[3:end_idx]
                    for line in frontmatter.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            metadata[key.strip()] = value.strip()

            # Then try to get additional metadata from info file
            content_hash = os.path.basename(content_path).split('_')[0]
            info_path = os.path.join(os.path.dirname(content_path), f"{content_hash}_info.txt")
            
            if os.path.exists(info_path):
                with open(info_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if ':' in line:
                            key, value = line.split(':', 1)
                            # Info file takes precedence over frontmatter
                            metadata[key.strip()] = value.strip()

            return metadata
            
        except Exception as e:
            logger.error(f"❌ Failed to get metadata: {str(e)}")
            return {}

    def _extract_main_content(self, content: str) -> str:
        """Extract just the main post content, focusing on the actual post text"""
        try:
            # Skip frontmatter
            if content.startswith('---'):
                end_idx = content.find('\n---', 3)
                if end_idx != -1:
                    content = content[end_idx + 4:].strip()

            # Extract the main content
            logger.debug("🔍 Starting content extraction")
            lines = content.split('\n')
            main_content_lines = []
            post_title = None
            content_started = False
            
            # First find the main post title
            for line in lines:
                if line.startswith('# ') and not line.startswith('## '):
                    post_title = line
                    content_started = True
                    logger.debug(f"📑 Found post title: {line}")
                    break

            # Then extract the actual content
            if content_started:
                logger.debug("📝 Extracting main content")
                # Process each line after the title
                for line in lines[lines.index(post_title) + 1:]:
                    # Stop at marker sections
                    if any(marker in line for marker in [
                        '[#',  # Hashtags
                        'You may also like',
                        'Related posts',
                        'See more comments',
                        'See more on the app',
                        '## Related',
                        '## Comments'
                    ]):
                        logger.debug(f"🛑 Stopped at marker: {line[:50]}")
                        break

                    # Skip UI elements and navigation
                    if any(skip in line for skip in [
                        'lemon8-app.com',
                        'Follow',
                        'followers',
                        'Open Lemon8',
                        'See more',
                        '1/'
                    ]):
                        continue

                    # Add the content line
                    main_content_lines.append(line)

            # Clean up the extracted content
            content = '\n'.join([post_title] + main_content_lines)
            content = re.sub(r'\n{3,}', '\n\n', content)  # Clean up multiple newlines
            content = re.sub(r'!\[.*?\]\(.*?\)', '', content)  # Remove image markdown
            content = re.sub(r'\[(?!#).*?\]\(.*?\)', '', content)  # Remove links except hashtags
            # Clean up any region identifiers that might be misleading the analysis
            content = re.sub(r'\?region=[a-z]{2}', '', content)  # Remove region parameters
            content = re.sub(r'Open in (the )?Lemon8.*$', '', content, flags=re.MULTILINE)  # Remove app references
            content = re.sub(r'@\w+\s+\|\s+\w+\s+follower.*$', '', content, flags=re.MULTILINE)  # Remove follower info
            content = content.strip()

            logger.debug(f"📊 Content statistics:")
            logger.debug(f"- Original length: {len(content)}")
            logger.debug(f"- Line count: {len(content.split(chr(10)))}")
            logger.debug("📄 Content preview:")
            logger.debug("-" * 40)
            logger.debug(content[:500] + "..." if len(content) > 500 else content)
            logger.debug("-" * 40)
            
            logger.info(f"📄 Extracted main content length: {len(content)} characters")
            return content.strip()
            
        except Exception as e:
            logger.error(f"❌ Failed to extract main content: {str(e)}")
            return ""

    def _clean_title_for_filename(self, title: str) -> str:
        """Clean title for use in filenames while preserving meaning"""
        # Remove invalid characters but preserve spaces and meaningful punctuation
        safe_chars = set(" -_()[]{}'")
        cleaned = "".join(c if c.isalnum() or c in safe_chars else "_" for c in title)
        
        # Clean up multiple underscores/spaces
        while "__" in cleaned:
            cleaned = cleaned.replace("__", "_")
        while "  " in cleaned:
            cleaned = cleaned.replace("  ", " ")
            
        cleaned = cleaned.strip(" _")
        
        if not cleaned:
            return "untitled"
            
        if len(cleaned) > 100:
            words = cleaned[:100].rsplit(' ', 1)[0]
            cleaned = words.strip(" _")
            
        return cleaned

    async def analyze_content(self, content_path: str) -> str:
        """Analyze content and generate markdown report"""
        logger.info(f"📊 Starting analysis for: {content_path}")
        
        try:
            # Read content
            with open(content_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata from both content and info file
            metadata = self._extract_metadata(content, content_path)
            
            # Extract main content
            main_content = self._extract_main_content(content)
            if not main_content:
                raise ValueError("Failed to extract main post content")
                
            # Get title with fallbacks
            raw_title = (
                metadata.get('title') or  # From frontmatter
                metadata.get('Title') or  # From info file
                'Untitled Post'  # Default
            )
            title_parts = raw_title.split(' | ')
            if len(title_parts) >= 3:
                post_title = title_parts[0]
                author = title_parts[1].replace('Gallery posted by ', '')
                title = f"{post_title} by {author}"
            else:
                title = raw_title
                
            safe_title = self._clean_title_for_filename(title)
            source_url = metadata.get('source')
            
            # Generate analysis from main content only
            analysis = await self._generate_analysis(main_content, source_url)
            
            # Get screenshot path
            content_hash = os.path.splitext(os.path.basename(content_path))[0].split('_')[0]
            screenshot_path = f"/{os.path.dirname(content_path)}/{content_hash}.png"
            
            # Build output markdown with debug info
            content_preview = main_content[:200] + "..." if len(main_content) > 200 else main_content
            report = f"""# {title}

![Screenshot]({screenshot_path})

{analysis}

---
Source: {source_url or '[Source URL not available]'}
Analyzed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Content Length: {len(main_content)} characters
Content Preview: {content_preview}
"""
            
            # Save report
            report_path = os.path.join(self.posts_dir, f"{safe_title}.md")
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
                
            logger.info(f"✅ Analysis completed: {report_path}")
            return report_path
            
        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            logger.error(error_msg)
            return error_msg

    async def _generate_analysis(self, content: str, source_url: str = None) -> str:
        """Generate structured analysis of content"""
        # Debug log the content being analyzed
        logger.debug("🔍 CONTENT BEING ANALYZED:")
        logger.debug("-" * 80)
        logger.debug(content[:500] + "..." if len(content) > 500 else content)
        logger.debug("-" * 80)

        prompt = PromptTemplate(
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

IMPORTANT: Create a detailed section for EACH location/activity listed above. Do not skip any locations mentioned in the original content.

## [Location/Activity Name 1]
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
![Supporting Image](relevant_detail_image)

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

---

[REQUIRED: Repeat the above detailed section structure for EVERY location/activity mentioned in the content. Each location must have its own complete section with all details.]

STRUCTURAL REQUIREMENTS:
1. Every location/activity listed in "Featured Locations/Activities" MUST have its own detailed section
2. Each section MUST maintain consistent formatting and detail level
3. DO NOT skip or summarize locations - give each one full treatment

LOCATION VALIDATION:
Before generating content:
1. Identify the primary country/region from the content
2. Use appropriate currency for that location
3. Use local terminology (e.g., "tube" for London underground, "subway" for US metro)
4. Reference local cultural context and customs
5. If content seems to drift to a different location, STOP and realign

QUALITY STANDARDS:
1. Prioritize accuracy and actionable information
2. Use natural, engaging language while maintaining professionalism
3. Include precise details (prices, times, locations)
4. Organize information in order of importance
5. Highlight unique aspects and insider tips
6. Maintain a balanced perspective, noting both positives and limitations
7. Ensure all images serve a purpose in understanding the location/activity"""
        )
        
        try:
            # Pass BOTH content and source_url to the template
            formatted_prompt = prompt.format(
                content=content,  # Use the content parameter passed to this method
                source_url=source_url or "[Source URL not available]"
            )
            
            # Debug log the full prompt
            logger.debug("📝 FULL PROMPT:")
            logger.debug("-" * 80)
            logger.debug(formatted_prompt)
            logger.debug("-" * 80)
            
            response = self.llm.invoke(formatted_prompt)
            
            if not hasattr(response, 'content'):
                raise ValueError("No content in response")
                
            return response.content
            
        except Exception as e:
            logger.error(f"❌ Analysis generation failed: {str(e)}")
            raise

    def get_report_title(self, report_path: str) -> str:
        """Get the original title from a report file"""
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Get first heading
                lines = content.split('\n')
                for line in lines:
                    if line.startswith('# '):
                        return line[2:].strip()
                return os.path.basename(report_path)
                
        except Exception as e:
            logger.error(f"❌ Failed to get report title: {str(e)}")
            return os.path.basename(report_path)
