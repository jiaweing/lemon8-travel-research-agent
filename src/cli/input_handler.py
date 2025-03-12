"""CLI input handling and validation."""

from typing import Dict, Tuple

class InputHandler:
    """Handles user input collection and validation."""

    # Content type options
    CONTENT_TYPES = {
        "1": {"name": "Everything", "keywords": ""},
        "2": {"name": "Food & Dining", "keywords": "food dining restaurants cafes"},
        "3": {"name": "Attractions & Activities", "keywords": "attractions sightseeing activities things to do"},
        "4": {"name": "Accommodation", "keywords": "hotels hostels accommodation airbnb where to stay"},
        "5": {"name": "Transport & Getting Around", "keywords": "transport subway bus train taxi getting around"},
        "6": {"name": "Local Tips & Culture", "keywords": "tips culture customs local insights"}
    }

    @staticmethod
    def show_welcome_message() -> None:
        """Display welcome message and instructions."""
        print("\n🌎 Lemon8 Travel Guide Generator")
        print("=" * 40)
        print("Create comprehensive travel guides from authentic experiences")
        print("=" * 40)

    @staticmethod
    def get_travel_query() -> str:
        """Get and validate travel query from user.

        Returns:
            str: Valid travel query
        """
        print("\n📍 What would you like to know?")
        print("Example queries:")
        print("- things to do in [city]")
        print("- best restaurants in [city]")
        print("- [city] travel guide")
        print("- hidden gems in [city]")
        print("- local food in [city]")
        
        query = input("\n🔍 Enter your travel query: ").strip()
        if not query or not any(char.isalpha() for char in query):
            raise ValueError("Please enter a valid travel query")
        
        return query

    @staticmethod
    def get_content_type() -> Dict[str, str]:
        """Get user's preferred type of travel content.

        Returns:
            Dict[str, str]: Selected content type configuration
        """
        print("\n🎯 What type of travel information are you looking for?")
        for key, content in InputHandler.CONTENT_TYPES.items():
            print(f"{key}. {content['name']}")
            
        choice = input("\nEnter number (1-6) or press Enter for everything: ").strip()
        return InputHandler.CONTENT_TYPES.get(choice, InputHandler.CONTENT_TYPES["1"])

    @staticmethod
    def get_source_count() -> int:
        """Get desired number of sources to analyze.

        Returns:
            int: Number of sources (minimum 5, default 15)
        """
        try:
            num_posts = input("\n📚 Minimum number of sources to analyze (default 15, min 5): ").strip()
            num_posts = int(num_posts) if num_posts else 15
            if num_posts < 5:
                print("⚠️ For reliable insights, we recommend analyzing at least 5 sources")
                num_posts = 5
            return num_posts
            
        except ValueError:
            print("⚠️ Using default: 15 sources")
            return 15

    @staticmethod
    def get_search_parameters() -> Tuple[str, Dict[str, str], int]:
        """Get all search parameters from user.

        Returns:
            Tuple[str, Dict[str, str], int]: (query, content_type, num_posts)
        """
        InputHandler.show_welcome_message()
        query = InputHandler.get_travel_query()
        content_type = InputHandler.get_content_type()
        num_posts = InputHandler.get_source_count()
        return query, content_type, num_posts
