"""Report file operations module."""

import os
import re
from typing import List, Tuple
from src.utils.logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger('ReportWriter')

class SearchReplaceBlock:
    """Represents a search/replace operation."""
    def __init__(self, search: str, replace: str):
        self.search = search.strip()
        self.replace = replace.strip()

    @classmethod
    def parse_blocks(cls, content: str) -> List['SearchReplaceBlock']:
        """Parse search/replace blocks from LLM response.
        
        Args:
            content: LLM response containing search/replace blocks
            
        Returns:
            List of SearchReplaceBlock objects
        """
        # Extract all search/replace blocks
        pattern = r'<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE'
        matches = re.finditer(pattern, content, re.DOTALL)
        
        blocks = []
        for match in matches:
            search = match.group(1)
            replace = match.group(2)
            blocks.append(cls(search, replace))
            
        return blocks

class ReportWriter:
    """Handles report file operations."""

    def __init__(self, output_dir: str, max_retries: int = 3):
        """Initialize the report writer.

        Args:
            output_dir (str): Base output directory
            max_retries (int): Maximum retries for search/replace operations
        """
        self.output_dir = output_dir.replace('\\', '/')
        self.max_retries = max_retries
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"📁 Initialized report writer with output_dir: {output_dir}")

    def update_report(self, report_path: str, llm_response: str) -> Tuple[bool, List[str]]:
        """Update report using search/replace blocks from LLM.
        
        Args:
            report_path: Path to report file
            llm_response: LLM response containing search/replace blocks
            
        Returns:
            Tuple of (success, list of failed operations)
        """
        report_path = report_path.replace('\\', '/')
        # Parse search/replace blocks
        blocks = SearchReplaceBlock.parse_blocks(llm_response)
        if not blocks:
            logger.warning("No valid search/replace blocks found in LLM response")
            return False, ["No valid search/replace blocks found"]
            
        # Read current report content
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read report: {e}")
            return False, [f"Failed to read report: {str(e)}"]
            
        # Track failed operations
        failed_ops = []
        updated = False
            
        # Process each block with retries
        for block in blocks:
            success = False
            error = None
            
            for attempt in range(self.max_retries):
                try:
                    # Attempt the replacement
                    new_content = self._try_replace(content, block.search, block.replace)
                    if new_content != content:
                        content = new_content
                        updated = True
                        success = True
                        break
                    error = "No match found"
                except Exception as e:
                    error = str(e)
                    logger.warning(f"Attempt {attempt + 1} failed: {error}")
                    
            if not success:
                failed_ops.append(f"Failed to replace '{block.search[:100]}...': {error}")
                    
        # Write updated content if any changes were made
        if updated:
            try:
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                logger.error(f"Failed to write updated report: {e}")
                return False, [f"Failed to write updated report: {str(e)}"]
                
        return len(failed_ops) == 0, failed_ops

    def _try_replace(self, content: str, search: str, replace: str) -> str:
        """Attempt a single search/replace operation.
        
        Args:
            content: Current report content
            search: Text to find
            replace: Text to replace with
            
        Returns:
            Updated content
        """
        # Use exact matching first
        if search in content:
            return content.replace(search, replace)
            
        # Try normalizing line endings and whitespace
        normalized_content = content.replace('\r\n', '\n')
        normalized_search = search.replace('\r\n', '\n')
        if normalized_search in normalized_content:
            return normalized_content.replace(normalized_search, replace)
            
        # If still no match, try flexible whitespace matching
        search_pattern = (re.escape(normalized_search)
                         .replace(r'\ ', r'\s+')
                         .replace(r'\n', r'\s*\n\s*'))
        result = re.sub(search_pattern, replace, normalized_content)  # Removed count=1 to replace all occurrences
        
        # Return original if no replacement made
        return result if result != normalized_content else content

    def write_report(self, content: str, query: str) -> str:
        """Write final report to file.

        Args:
            content (str): Report content to write
            query (str): Search query for filename

        Returns:
            str: Path to written report file
        """
        try:
            # Generate report path with forward slashes
            report_path = self._get_report_path(query).replace('\\', '/')
            
            # Write content
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            logger.info(f"✅ Report saved to: {report_path}")
            return report_path

        except Exception as e:
            error_msg = f"❌ Failed to write report: {str(e)}"
            logger.error(error_msg)
            raise

    def _get_report_path(self, query: str) -> str:
        """Generate path for report file.

        Args:
            query (str): Search query to use in filename

        Returns:
            str: Report file path
        """
        # Sanitize query for filename
        safe_query = self._sanitize_filename(query).lower()
        return os.path.join(self.output_dir, f"{safe_query}.md")

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Clean filename for safe file system use.

        Args:
            filename (str): Original filename

        Returns:
            str: Sanitized filename
        """
        # Remove invalid characters but preserve meaningful ones
        safe_chars = set(" -_()[]")
        cleaned = "".join(c if c.isalnum() or c in safe_chars else "_" for c in filename)
        
        # Clean up multiple underscores/spaces
        while "__" in cleaned:
            cleaned = cleaned.replace("__", "_")
        while "  " in cleaned:
            cleaned = cleaned.replace("  ", " ")
            
        # Convert spaces to underscores
        cleaned = cleaned.replace(" ", "_")
            
        # Trim and enforce length limit
        cleaned = cleaned.strip("_")
        if len(cleaned) > 100:
            cleaned = cleaned[:100].rsplit("_", 1)[0].strip()
            
        # Ensure we have a valid filename
        if not cleaned:
            cleaned = "report"
            
        return cleaned

    def append_to_report(self, report_path: str, content: str) -> None:
        """Append content to existing report.

        Args:
            report_path (str): Path to report file
            content (str): Content to append
        """
        report_path = report_path.replace('\\', '/')
        try:
            with open(report_path, "a", encoding="utf-8") as f:
                f.write(f"\n\n{content}")
            logger.debug(f"✅ Content appended to: {report_path}")

        except Exception as e:
            logger.error(f"❌ Failed to append to report: {str(e)}")
            raise
