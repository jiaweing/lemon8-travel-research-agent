"""
Lemon8 Travel Guide Generator

An intelligent CLI tool that generates comprehensive travel guides by analyzing authentic Lemon8 content.
Extracts and aggregates real user experiences, recommendations, and local insights.

Example:
    python src/main.py
    > Enter travel query: things to do in london
    > Generating travel guide...
"""

import asyncio
import os
import sys
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# Add src directory to Python path when running from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.lemon8_scraper import Lemon8ScraperAgent
from src.agents.lemon8_analyzer import Lemon8AnalyzerAgent
from src.agents.report_aggregator import ReportAggregatorAgent
from src.agents.lemon8_relevance_checker import Lemon8RelevanceCheckerAgent
from src.config import Config
from src.utils.logging_config import setup_logging, get_logger

# Setup logging with emojis for better visibility
setup_logging()
logger = get_logger('main')

class Lemon8TravelCLI:
    """
    Command-line interface for generating travel guides from Lemon8 content.
    
    Provides an interactive way to get authentic travel recommendations by analyzing
    real user experiences and reviews from Lemon8 posts.
    """
    
    # Travel content categories
    CONTENT_TYPES = {
        "1": {"name": "Everything", "keywords": ""},
        "2": {"name": "Food & Dining", "keywords": "food dining restaurants cafes"},
        "3": {"name": "Attractions & Activities", "keywords": "attractions sightseeing activities things to do"},
        "4": {"name": "Accommodation", "keywords": "hotels hostels accommodation airbnb where to stay"},
        "5": {"name": "Transport & Getting Around", "keywords": "transport subway bus train taxi getting around"},
        "6": {"name": "Local Tips & Culture", "keywords": "tips culture customs local insights"}
    }
    
    def __init__(self) -> None:
        """Initialize the CLI with all required agents."""
        Config.validate()  # Ensure configuration is valid
        self.relevance_checker = Lemon8RelevanceCheckerAgent()
        logger.info("🤖 Initialized Lemon8 Travel Guide Generator")

    def _clean_query_for_path(self, query: str) -> str:
        """Clean query for use in file paths"""
        # Replace spaces and special chars with underscores
        cleaned = re.sub(r'[^\w\s-]', '_', query)
        cleaned = re.sub(r'[-\s]+', '_', cleaned)
        # Limit length and remove trailing underscores
        return cleaned[:50].strip('_').lower()

    def _init_agents(self, query: str) -> None:
        """Initialize agents with query-specific run ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = self._clean_query_for_path(query)
        self.run_id = f"{safe_query}_{timestamp}"
        self.output_dir = os.path.join("output", self.run_id)
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.scraper = Lemon8ScraperAgent(run_id=self.run_id)
        self.analyzer = Lemon8AnalyzerAgent(run_id=self.run_id)

    def _select_content_type(self) -> Dict[str, str]:
        """Get user's preferred type of travel content."""
        print("\n🎯 What type of travel information are you looking for?")
        for key, content in self.CONTENT_TYPES.items():
            print(f"{key}. {content['name']}")
            
        choice = input("\nEnter number (1-6) or press Enter for everything: ").strip()
        return self.CONTENT_TYPES.get(choice, self.CONTENT_TYPES["1"])

    async def _scrape_posts(self, posts: List[str], query: str, content_type: Dict[str, str], min_posts: int) -> List[Dict[str, str]]:
        """
        Scrape content with progress tracking and content type filtering.
        
        Args:
            posts: List of post URLs to scrape
            query: Original search query
            content_type: Selected content type with keywords
            min_posts: Minimum number of relevant posts needed
        """
        results = []
        to_scrape = list(posts)
        seen_urls = set(posts)
        relevant_count = 0
        
        # Combine original query with content type keywords if specific type selected
        enhanced_query = f"{query} {content_type['keywords']}" if content_type['keywords'] else query
        
        while to_scrape and relevant_count < min_posts:
            post_url = to_scrape.pop(0)
            print(f"\n📥 Analyzing post: {post_url}")
            
            try:
                result = await self.scraper.scrape_post(post_url)
                if result:
                    print(f"📄 Content saved: {os.path.basename(result['content_path'])}")
                    
                    # Check both topic and travel relevance
                    is_relevant, score, reason = await self.relevance_checker.check_relevance(
                        result['content_path'], 
                        enhanced_query,
                        threshold=0.6
                    )
                    
                    result.update({
                        'relevance_score': score,
                        'relevance_reason': reason,
                        'is_relevant': is_relevant
                    })
                    results.append(result)
                    
                    if is_relevant:
                        relevant_count += 1
                        print(f"✅ [{relevant_count}/{min_posts}] Relevant content found (score: {score:.2f})")
                        print(f"💡 Value: {reason}")
                        
                        # Add related posts to queue
                        if 'related_posts' in result:
                            new_posts = [url for url in result['related_posts'] if url not in seen_urls]
                            if new_posts:
                                print(f"🔗 Found {len(new_posts)} more potential sources")
                                to_scrape.extend(new_posts)
                                seen_urls.update(new_posts)
                    else:
                        print(f"⏩ Content not relevant (score: {score:.2f})")
                        print(f"📝 Reason: {reason}")
                else:
                    print(f"❌ Failed to analyze post")
                    
            except Exception as e:
                logger.error(f"❌ Error processing post: {str(e)}")
                
        return results

    async def run(self) -> None:
        """Run the travel guide generation process."""
        try:
            # Welcome message
            print("\n🌎 Lemon8 Travel Guide Generator")
            print("=" * 40)
            print("Create comprehensive travel guides from authentic experiences")
            print("=" * 40)
            
            # Get travel query
            print("\n📍 What would you like to know?")
            print("Example queries:")
            print("- things to do in [city]")
            print("- best restaurants in [city]")
            print("- [city] travel guide")
            print("- hidden gems in [city]")
            print("- local food in [city]")
            
            query = input("\n🔍 Enter your travel query: ").strip()
            if not query or not any(char.isalpha() for char in query):
                print("❌ Please enter a valid travel query")
                return
            
            # Get content preferences
            content_type = self._select_content_type()
            
            # Get number of sources
            try:
                num_posts = input("\n📚 Minimum number of sources to analyze (default 15, min 5): ").strip()
                num_posts = int(num_posts) if num_posts else 15
                if num_posts < 5:
                    print("⚠️ For reliable insights, we recommend analyzing at least 5 sources")
                    num_posts = 5
            except ValueError:
                print("⚠️ Using default: 15 sources")
                num_posts = 15
            
            # Initialize agents with query-specific run ID
            self._init_agents(query)
            
            # Start the process
            print(f"\n🚀 Generating...")
            print(f"📋 Focus: {content_type['name']}")
            print(f"🎯 Target: {num_posts}+ authentic sources")
            print(f"📂 Output directory: {self.output_dir}")
            
            # Find relevant posts
            posts = await self.scraper.scrape_search_results(query, max_posts=num_posts)
            if not posts:
                print("❌ No relevant content found")
                return
                
            print(f"✨ Found {len(posts)} potential sources")
            
            # Analyze posts
            results = await self._scrape_posts(posts, query, content_type, num_posts)
            relevant_results = [r for r in results if r.get('is_relevant', False)]
            
            # Summary before detailed analysis
            successful = len(results)
            relevant = len(relevant_results)
            
            print(f"\n📊 Content Analysis Summary")
            print("=" * 30)
            print(f"✅ Sources analyzed: {successful}")
            print(f"🎯 Relevant content: {relevant}")
            print(f"⭐ Average relevance: {sum(r['relevance_score'] for r in relevant_results) / relevant:.2f}")
            
            if relevant > 0:
                print("\n📝 Generating detailed travel insights...")
                report_paths = []
                
                # Analyze each relevant post
                for result in relevant_results:
                    if 'content_path' in result:
                        try:
                            report_path = await self.analyzer.analyze_content(result['content_path'])
                            report_paths.append(report_path)
                            print(f"✅ Processed: {os.path.basename(result['content_path'])}")
                        except Exception as e:
                            logger.error(f"❌ Analysis failed: {str(e)}")
                
                # Generate final travel guide
                if report_paths:
                    print("\n🏗️ Creating your travel guide...")
                    aggregator = ReportAggregatorAgent(run_id=self.run_id)
                    guide_path = await aggregator.generate_final_report(query)
                    print(f"\n🎉 Your travel guide is ready!")
                    print(f"📔 Guide saved to: {guide_path}")
                    print(f"\n📂 All outputs saved to: {self.output_dir}")
                    print("\nOpen the guide in your favorite Markdown viewer to explore:")
                    print(f"- 🗺️ Detailed recommendations")
                    print(f"- 💰 Cost information")
                    print(f"- 🚇 Transport options")
                    print(f"- 💡 Local tips and insights")
                    print(f"- ⚠️ Important travel notes")
                
        except KeyboardInterrupt:
            print("\n\n⚠️ Guide generation interrupted")
        except Exception as e:
            logger.error(f"❌ Error: {str(e)}")

def main() -> None:
    """Launch the Lemon8 Travel Guide Generator."""
    cli = Lemon8TravelCLI()
    asyncio.run(cli.run())

if __name__ == "__main__":
    main()
