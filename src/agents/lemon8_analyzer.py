from typing import Dict, List, Optional, Tuple
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
            temperature=0.7,
        )

    def _get_content_title(self, content_path: str) -> str:
        """Extract content title from metadata file"""
        try:
            # Get hash from content path
            content_hash = os.path.basename(content_path).split('_')[0]
            
            # Find corresponding info file
            info_path = os.path.join(os.path.dirname(content_path), f"{content_hash}_info.txt")
            
            if os.path.exists(info_path):
                with open(info_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('Title:'):
                            title = line.replace('Title:', '').strip()
                            if title and title.lower() != 'no title':
                                return title
            
            logger.warning(f"⚠️ No title found in metadata for {content_path}")
            return "untitled"
            
        except Exception as e:
            logger.error(f"❌ Failed to get content title: {str(e)}")
            return "untitled"

    def _clean_title_for_filename(self, title: str) -> str:
        """Clean title for use in filenames while preserving meaning"""
        # Remove invalid characters but preserve spaces and meaningful punctuation
        safe_chars = set(" -_()[]{}'")  # Allow these special characters
        cleaned = "".join(c if c.isalnum() or c in safe_chars else "_" for c in title)
        
        # Clean up multiple underscores/spaces
        while "__" in cleaned:
            cleaned = cleaned.replace("__", "_")
        while "  " in cleaned:
            cleaned = cleaned.replace("  ", " ")
            
        # Remove leading/trailing spaces and underscores
        cleaned = cleaned.strip(" _")
        
        # If title becomes empty after cleaning, return untitled
        if not cleaned:
            return "untitled"
            
        # Limit length while trying to keep whole words
        if len(cleaned) > 100:
            words = cleaned[:100].rsplit(' ', 1)[0]
            cleaned = words.strip(" _")
            
        return cleaned

    def _extract_frontmatter(self, content: str) -> Tuple[Dict[str, str], str]:
        """Extract YAML frontmatter and remaining content"""
        frontmatter = {}
        main_content = content
        
        # Check for YAML frontmatter
        if content.startswith('---'):
            try:
                # Find end of frontmatter
                end_idx = content.find('\n---', 3)
                if end_idx != -1:
                    frontmatter_str = content[3:end_idx]
                    main_content = content[end_idx + 4:].strip()
                    
                    # Parse frontmatter
                    for line in frontmatter_str.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            frontmatter[key.strip()] = value.strip()
            except Exception as e:
                logger.warning(f"Failed to parse frontmatter: {str(e)}")
        
        return frontmatter, main_content

    async def analyze_content(self, content_path: str) -> str:
        """Analyze content and generate markdown report"""
        logger.info(f"📊 Starting analysis for: {content_path}")
        
        try:
            # Read content
            with open(content_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract frontmatter and main content
            frontmatter, main_content = self._extract_frontmatter(content)
            
            # Extract and clean title from metadata
            raw_title = frontmatter.get('title') or self._get_content_title(content_path)
            
            # Format title: remove " | Gallery posted by" and " | Lemon8", add "by" before author
            title_parts = raw_title.split(' | ')
            if len(title_parts) >= 3:
                post_title = title_parts[0]
                author = title_parts[1].replace('Gallery posted by ', '')
                title = f"{post_title} by {author}"
            else:
                title = raw_title
                
            safe_title = self._clean_title_for_filename(title)
            
            # Get source URL from frontmatter
            source_url = frontmatter.get('source')
            
            # Generate analysis with source URL
            analysis = await self._generate_analysis(main_content, source_url)
            
            # Reconstruct frontmatter
            frontmatter['title'] = title
            frontmatter['analyzed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Format frontmatter section
            frontmatter_lines = ['---']
            for key, value in frontmatter.items():
                frontmatter_lines.append(f'{key}: {value}')
            frontmatter_lines.append('---\n')
            
            # Get content hash and construct screenshot path using forward slashes
            content_hash = os.path.splitext(os.path.basename(content_path))[0].split('_')[0]
            screenshot_path = f"/{os.path.dirname(content_path)}/{content_hash}.png"
            
            # Combine all parts with screenshot (ensure forward slashes in path)
            markdown_parts = [
                *frontmatter_lines,
                f"# {title}",
                "", # Empty line for spacing
                f"![Screenshot]({screenshot_path})",
                "", # Empty line for spacing
                analysis
            ]
            full_content = '\n'.join(markdown_parts)
            
            # Save report in posts directory
            report_path = os.path.join(self.posts_dir, f"{safe_title}.md")
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(full_content)
                
            logger.info(f"✅ Analysis completed: {report_path}")
            return report_path
            
        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            logger.error(error_msg)
            return error_msg

    async def _generate_analysis(self, content: str, source_url: str = None) -> str:
        """Generate structured analysis of content"""
        prompt = PromptTemplate(
            input_variables=["content", "source_url"],
        template="""You are a professional content analyst specializing in location-based reviews and recommendations. Your task is to analyze content and extract valuable insights in a structured, engaging format.

INPUT RULES:
- Process all content before any "Related posts" section
- Preserve all tiktokcdn.com image URLs in their original format
- Extract key metrics (likes, saves, comments, followers) for the overview
- Identify primary and secondary locations/activities
- Note price points, operational hours, and practical details
- Pay attention to author's personal experiences and recommendations

OUTPUT FORMAT:

# Overview
[Write a compelling 2-3 sentence summary that captures the essence of the post and its unique value proposition]

_Source: {source_url}_

### Engagement Analysis 📊
- **Community Response:** [X] Likes • [X] Saves • [X] Comments
- **Creator Impact:** [X] Followers • [Brief note on creator's authority in this topic]
- **Content Quality:** [High/Medium/Low - based on detail level, image quality, usefulness]

### Key Discoveries 🗺
[Bullet list of 3-5 main locations/activities, each with a one-line value proposition]
- [Name]: [What makes it special/worth visiting]

---

## [Primary Location/Activity Name]
![Representative Image](best_quality_image_url)

**Essential Info:**
- 📍 Location: [Detailed address + Alternative names if applicable]
- ⏰ Hours: [Operating hours + Best timing recommendations]
- 💰 Price Range: [Cost breakdown in SGD + Value assessment]
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

[Repeat structure for additional locations if present, maintaining consistent formatting]

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
            # Generate analysis
            formatted_prompt = prompt.format(content=content, source_url=source_url or "[Source URL not available]")
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
                
                # First try to get title from frontmatter
                if content.startswith('---'):
                    frontmatter, _ = self._extract_frontmatter(content)
                    if 'title' in frontmatter:
                        return frontmatter['title']
                
                # Then try first heading
                lines = content.split('\n')
                for line in lines:
                    if line.startswith('# '):
                        return line[2:].strip()
                
                # Fallback to filename
                return os.path.basename(report_path).rsplit('_', 2)[0]
                
        except Exception as e:
            logger.error(f"❌ Failed to get report title: {str(e)}")
            return os.path.basename(report_path).rsplit('_', 2)[0]
