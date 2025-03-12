"""Lemon8 Travel Guide Generator.

An intelligent CLI tool that generates comprehensive travel guides by analyzing authentic Lemon8 content.
Extracts and aggregates real user experiences, recommendations, and local insights.

Example:
    python src/main.py
    > Enter travel query: things to do in london
    > Generating travel guide...
"""

import os
import sys
import asyncio

# Add src directory to Python path when running from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cli.travel_cli import Lemon8TravelCLI
from src.utils.logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger('main')

def main() -> None:
    """Launch the Lemon8 Travel Guide Generator."""
    try:
        cli = Lemon8TravelCLI()
        asyncio.run(cli.run())
    except Exception as e:
        logger.error(f"❌ Application error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
