"""Main CLI orchestration for travel guide generation."""

import os
import re
from datetime import datetime
from typing import List, Dict, Optional
from src.agents.lemon8_scraper import Lemon8ScraperAgent
from src.agents.lemon8_analyzer import Lemon8AnalyzerAgent
from src.agents.report_aggregator import ReportAggregatorAgent
from src.agents.lemon8_relevance_checker import Lemon8RelevanceCheckerAgent
from src.config import Config
from src.utils.logging_config import setup_logging, get_logger
from .input_handler import InputHandler
from .progress_tracker import ProgressTracker

# Setup logging
setup_logging()
logger = get_logger('TravelCLI')

class Lemon8TravelCLI:
    """Main CLI for generating travel guides from Lemon8 content."""

    def __init__(self) -> None:
        """Initialize the CLI with required agents."""
        Config.validate()  # Ensure configuration is valid
        self.relevance_checker = Lemon8RelevanceCheckerAgent()
        logger.info("🤖 Initialized Lemon8 Travel Guide Generator")

    def _clean_query_for_path(self, query: str) -> str:
        """Clean query for use in file paths.

        Args:
            query (str): Raw query string

        Returns:
            str: Clean path-safe string
        """
        cleaned = re.sub(r'[^\w\s-]', '_', query)
        cleaned = re.sub(r'[-\s]+', '_', cleaned)
        return cleaned[:50].strip('_').lower()

    def _init_agents(self, query: str) -> None:
        """Initialize agents with query-specific run ID.

        Args:
            query (str): Search query
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = self._clean_query_for_path(query)
        self.run_id = f"{safe_query}_{timestamp}"
        self.output_dir = os.path.join("output", self.run_id)
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.scraper = Lemon8ScraperAgent(run_id=self.run_id)
        self.analyzer = Lemon8AnalyzerAgent(run_id=self.run_id)

    async def _scrape_posts(
        self,
        posts: List[str],
        query: str,
        content_type: Dict[str, str],
        progress: ProgressTracker
    ) -> List[Dict]:
        """Scrape and analyze posts with progress tracking.

        Args:
            posts (List[str]): List of post URLs
            query (str): Search query
            content_type (Dict[str, str]): Selected content type
            progress (ProgressTracker): Progress tracker

        Returns:
            List[Dict]: Analysis results
        """
        results = []
        to_scrape = list(posts)
        seen_urls = set(posts)
        
        # Enhanced query with content type keywords
        enhanced_query = f"{query} {content_type['keywords']}" if content_type['keywords'] else query
        
        while (to_scrape and 
               progress.relevant_posts < progress.target_posts and 
               progress.sources_reviewed < progress.max_sources):
            
            post_url = to_scrape.pop(0)
            print(f"\n📥 Analyzing post: {post_url}")
            
            try:
                # Scrape post
                result = await self.scraper.scrape_post(post_url)
                if not result:
                    logger.error(f"❌ Failed to analyze post")
                    continue

                print(f"📄 Content saved: {os.path.basename(result['content_path'])}")
                
                # Check relevance
                is_relevant, score, reason = await self.relevance_checker.check_relevance(
                    result['content_path'], 
                    enhanced_query,
                    threshold=0.6
                )
                
                # Update result and track progress
                result.update({
                    'relevance_score': score,
                    'relevance_reason': reason,
                    'is_relevant': is_relevant
                })
                results.append(result)
                
                # Find new sources from related posts
                new_sources = 0
                if is_relevant and 'related_posts' in result:
                    new_posts = [url for url in result['related_posts'] if url not in seen_urls]
                    if new_posts:
                        to_scrape.extend(new_posts)
                        seen_urls.update(new_posts)
                        new_sources = len(new_posts)
                
                # Update progress display
                progress.update_source_progress(
                    url=post_url,
                    is_relevant=is_relevant,
                    score=score,
                    reason=reason,
                    new_sources=new_sources
                )
                    
            except Exception as e:
                logger.error(f"❌ Error processing post: {str(e)}")
                
        return results

    async def _generate_guide(self, results: List[Dict], query: str) -> Optional[str]:
        """Generate final travel guide from results.

        Args:
            results (List[Dict]): Analysis results
            query (str): Search query

        Returns:
            Optional[str]: Path to generated guide or None on failure
        """
        try:
            print("\n📝 Generating detailed travel insights...")
            report_paths = []
            
            # Analyze each relevant post
            relevant_results = [r for r in results if r.get('is_relevant', False)]
            for result in relevant_results:
                if 'content_path' in result:
                    try:
                        report_path = await self.analyzer.analyze_content(result['content_path'])
                        report_paths.append(report_path)
                        print(f"✅ Processed: {os.path.basename(result['content_path'])}")
                    except Exception as e:
                        logger.error(f"❌ Analysis failed: {str(e)}")
            
            # Generate final guide
            if report_paths:
                print("\n🏗️ Creating your travel guide...")
                aggregator = ReportAggregatorAgent(run_id=self.run_id)
                return await aggregator.generate_final_report(query)
            
            return None

        except Exception as e:
            logger.error(f"❌ Guide generation failed: {str(e)}")
            return None

    async def run(self) -> None:
        """Run the travel guide generation process."""
        try:
            # Get user input
            query, content_type, num_posts = InputHandler.get_search_parameters()
            
            # Initialize agents and tracker
            self._init_agents(query)
            progress = ProgressTracker(
                query=query,
                content_type=content_type,
                target_posts=num_posts
            )
            progress.show_initial_config(self.run_id, self.output_dir)
            
            # Find relevant posts
            posts = await self.scraper.scrape_search_results(query, max_posts=num_posts)
            if not posts:
                print("❌ No relevant content found")
                return
            
            print(f"✨ Found {len(posts)} potential sources")
            
            # Analyze posts
            results = await self._scrape_posts(posts, query, content_type, progress)
            progress.show_analysis_summary(results)
            
            # Generate final guide
            if any(r.get('is_relevant', False) for r in results):
                guide_path = await self._generate_guide(results, query)
                if guide_path:
                    progress.show_final_summary(guide_path, self.output_dir)
                
        except KeyboardInterrupt:
            print("\n\n⚠️ Guide generation interrupted")
        except Exception as e:
            logger.error(f"❌ Error: {str(e)}")
