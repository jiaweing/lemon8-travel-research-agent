from typing import List, Dict
import os
from datetime import datetime
from crewai import Agent
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from src.utils.logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger('ReportAggregator')

class ReportAggregatorAgent:
    def __init__(self, run_id: str = None):
        """Initialize the report aggregator agent"""
        logger.info("🤖 Initializing ReportAggregatorAgent")
        self.run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = os.path.join("output", self.run_id)
        self.posts_dir = os.path.join(self.output_dir, "posts")
        # Create required directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.posts_dir, exist_ok=True)
        
        self.agent = Agent(
            role='Content Aggregator',
            goal='Create comprehensive summaries from multiple content sources',
            backstory="""You are an expert content aggregator that analyzes multiple reports
            to create detailed summaries. You identify patterns in recommendations,
            cross-validate information, and create ranked suggestions based on authentic sources."""
        )
        self.llm = self._init_llm()
        
        # Initialize the prompt template for iterative refinement
        self.refine_prompt = PromptTemplate(
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

    def _init_llm(self) -> ChatOpenAI:
        """Initialize LLM with consistent configuration"""
        logger.info("🔧 Initializing LLM")
        try:
            llm = ChatOpenAI(
                model_name="gpt-4o-mini",
                temperature=0.7,
            )
            logger.info("✅ LLM initialized")
            return llm
        except Exception as e:
            logger.error(f"❌ LLM initialization failed: {str(e)}")
            raise

    def _load_reports(self, batch_size: int = 5) -> List[List[Dict[str, str]]]:
        """Load reports in batches"""
        logger.info(f"📂 Loading posts from {self.posts_dir}")
        try:
            all_reports = []
            batch = []
            
            for filename in sorted(os.listdir(self.posts_dir)):
                if filename.endswith('.md'):
                    with open(os.path.join(self.posts_dir, filename), 'r', encoding='utf-8') as f:
                        report = {
                            'content': f.read(),
                            'filename': filename
                        }
                        batch.append(report)
                        
                    if len(batch) >= batch_size:
                        all_reports.append(batch)
                        batch = []
                        
            if batch:
                all_reports.append(batch)
                
            logger.info(f"📄 Loaded {sum(len(batch) for batch in all_reports)} reports in {len(all_reports)} batches")
            return all_reports
        except Exception as e:
            logger.error(f"❌ Failed to load reports: {str(e)}")
            raise

    async def _refine_report(self, query: str, current_report: str, batch_content: str) -> str:
        """Use LLM to iteratively refine the report with new information"""
        try:
            formatted_prompt = self.refine_prompt.format(
                query=query,
                current_report=current_report,
                new_reports=batch_content
            )
            
            response = self.llm.invoke(formatted_prompt)
            if not hasattr(response, 'content'):
                logger.error("❌ Report refinement failed")
                return current_report
                
            return response.content
            
        except Exception as e:
            logger.error(f"❌ Report refinement failed: {str(e)}")
            return current_report

    async def generate_final_report(self, query: str) -> str:
        """Generate a final consolidated report for the query"""
        logger.info(f"📊 Starting report generation for: {query}")
        
        # Load reports in batches
        report_batches = self._load_reports()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Sanitize query for filename
        safe_query = "".join(c if c.isalnum() or c in " -_" else "_" for c in query)
        safe_query = safe_query.replace(" ", "_")[:100]
        final_report_path = os.path.join(self.output_dir, f"{safe_query}.md")
        
        try:
            # Start with a structured report template
            current_report = f"""# {query}

A guide to help you explore the best cafes and restaurants.

"""
            
            # Process each batch and iteratively improve the report
            for i, batch in enumerate(report_batches, 1):
                logger.info(f"🔄 Processing batch {i} of {len(report_batches)}")
                
                batch_content = "\n\n---\n\n".join(
                    f"Report {j+1}:\n{report['content']}"
                    for j, report in enumerate(batch)
                )
                
                # Refine the report with new information
                current_report = await self._refine_report(query, current_report, batch_content)
            
            # Save final report
            with open(final_report_path, "w", encoding="utf-8") as f:
                f.write(current_report)
            
            logger.info(f"✅ Report completed at {final_report_path}")
            return final_report_path
            
        except Exception as e:
            error_msg = f"Report generation failed: {str(e)}"
            logger.error(error_msg)
            return error_msg
