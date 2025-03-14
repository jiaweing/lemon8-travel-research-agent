"""Progress tracking and reporting for guide generation."""

from typing import List, Dict
from src.utils.logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger('ProgressTracker')

class ProgressTracker:
    """Tracks and reports progress during guide generation."""

    def __init__(self, query: str, content_type: Dict[str, str], target_posts: int, multiplier: int = 10):
        """Initialize the progress tracker.

        Args:
            query (str): Search query
            content_type (Dict[str, str]): Selected content type
            target_posts (int): Target number of relevant posts
            multiplier (int, optional): Max sources multiplier. Defaults to 10.
        """
        self.query = query
        self.content_type = content_type
        self.target_posts = target_posts
        self._initial_max = target_posts * multiplier  # Store initial max for reference
        self.max_sources = self._initial_max
        self.sources_reviewed = 0
        self.relevant_posts = 0

    def update_max_sources(self, total_sources: int) -> None:
        """Update the maximum number of sources after crawling.

        Args:
            total_sources (int): Total number of sources found during crawling
        """
        self.max_sources = total_sources

    def show_initial_config(self, run_id: str, output_dir: str) -> None:
        """Display initial configuration.

        Args:
            run_id (str): Current run identifier
            output_dir (str): Output directory path
        """
        print(f"\n🚀 Generating...")
        print(f"🔍 Query: {self.query}")
        print(f"📋 Focus: {self.content_type['name']}")
        print(f"🎯 Target: {self.target_posts}+ authentic sources")
        print(f"🔗 Maximum sources: {self.max_sources} ({self.max_sources/self.target_posts:.0f}x)")
        print(f"🔗 Run ID: {run_id}")
        print(f"📂 Output directory: {output_dir}")

    def update_source_progress(
        self,
        url: str,
        is_relevant: bool,
        score: float,
        reason: str,
        new_sources: int = 0
    ) -> None:
        """Update and display source analysis progress.

        Args:
            url (str): Source URL
            is_relevant (bool): Whether source was relevant
            score (float): Relevance score
            reason (str): Relevance explanation
            new_sources (int, optional): Number of new sources found. Defaults to 0.
        """
        self.sources_reviewed += 1
        if is_relevant:
            self.relevant_posts += 1
            print(f"\n✅ [{self.relevant_posts}/{self.target_posts}] Relevant content found (score: {score:.2f})")
            print(f"💡 Value: {reason}")
            if new_sources:
                print(f"🔗 Found {new_sources} more potential sources")
        else:
            print(f"\n⏩ Content not relevant (score: {score:.2f})")
            print(f"📝 Reason: {reason}")

        # Show overall progress
        print(f"📊 Progress: {self.sources_reviewed}/{self.max_sources} sources reviewed "
              f"({(self.sources_reviewed/self.max_sources)*100:.1f}%)")

    def show_analysis_summary(self, results: List[Dict]) -> None:
        """Display summary of content analysis.

        Args:
            results (List[Dict]): List of analysis results
        """
        relevant_results = [r for r in results if r.get('is_relevant', False)]
        relevant_count = len(relevant_results)
        
        print(f"\n📊 Content Analysis Summary")
        print("=" * 30)
        print(f"✅ Sources analyzed: {self.sources_reviewed}/{self.max_sources}")
        print(f"🎯 Relevant content: {relevant_count}/{self.target_posts}")
        if relevant_count > 0:
            avg_score = sum(r['relevance_score'] for r in relevant_results) / relevant_count
            print(f"⭐ Average relevance: {avg_score:.2f}")
        print(f"📊 Progress: {(self.sources_reviewed/self.max_sources)*100:.1f}% of required sources reviewed")

    def show_final_summary(self, guide_path: str, output_dir: str) -> None:
        """Display final generation summary.

        Args:
            guide_path (str): Path to generated guide
            output_dir (str): Output directory path
        """
        print(f"\n🎉 Your travel guide is ready!")
        print(f"📔 Guide saved to: {guide_path}")
        print(f"\n📂 All outputs saved to: {output_dir}")
        print("\nOpen the guide in your favorite Markdown viewer to explore:")
        print(f"- 🗺️ Detailed recommendations")
        print(f"- 💰 Cost information")
        print(f"- 🚇 Transport options")
        print(f"- 💡 Local tips and insights")
        print(f"- ⚠️ Important travel notes")
