# 🌎 Lemon8 Travel Guide Generator

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![crawl4ai](https://img.shields.io/badge/crawl4ai-0.5.0.post4-green.svg)](https://pypi.org/project/crawl4ai/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A team of agents that scrapes and analyzes authentic user experiences from Lemon8, and generates comprehensive travel guides. Get real recommendations, local insights, and practical travel information based on crowdsourced content.

## ✨ Key Features

- 🎯 **Travel-Focused Analysis** - Smart filtering and scoring of travel-related content
- 🗺️ **Comprehensive Guides** - Detailed information about destinations, including:
  - Accommodations and places to stay
  - Food and dining recommendations
  - Activities and attractions
  - Transport options and accessibility
  - Local tips and cultural insights
  - Cost information and budgeting
- 📸 **Visual Content** - Organized photos of locations, food, and accommodations
- 💡 **Local Knowledge** - Authentic tips and recommendations from real travelers
- ⚠️ **Travel Alerts** - Important warnings and seasonal considerations
- 🔄 **Cross-Validation** - Information verified across multiple sources

## 🚀 Quick Start

### Installation

1. **Set up the environment** (requires Python 3.11+):

   ```bash
   # Using poetry (recommended)
   poetry install

   # Or using pip
   pip install -r requirements.txt
   ```

2. **Configure settings**:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your settings.

## 📋 Project Structure

```
.
├── src/
│   ├── agents/
│   │   ├── lemon8_scraper.py         # Content scraping
│   │   ├── lemon8_analyzer.py        # Travel content analysis
│   │   ├── lemon8_relevance_checker.py  # Travel relevance scoring
│   │   └── report_aggregator.py      # Travel guide generation
│   ├── config.py                     # Configuration management
│   ├── utils/
│   │   └── logging_config.py         # Logging configuration
│   └── main.py                       # CLI interface
├── logs/                            # Application logs
├── output/                          # Generated content & guides
├── requirements.txt                 # Python dependencies
└── pyproject.toml                  # Project metadata
```

## Key Dependencies

- crawl4ai (0.5.0.post4) - Web crawling and content extraction
- crewai (0.105.0) - Agent orchestration and coordination
- langchain (0.3.20) - LLM integration and chaining
- langchain-openai (0.3.7) - OpenAI model support
- beautifulsoup4 (4.12.3) - HTML parsing
- markdown (3.5.2) - Markdown processing
- pillow (10.4.0) - Image handling

## 💡 Usage Examples

### Generate a Travel Guide

```bash
python src/main.py
```

The interactive CLI will guide you through:

1. **Travel Query**: Enter what you want to know

   ```
   Example queries:
   - things to do in [city]
   - best restaurants in [city]
   - [city] travel guide
   - hidden gems in [city]
   - local food in [city]
   ```

2. **Content Type Selection**: Choose your focus

   ```
   1. Everything - Comprehensive destination guide
   2. Food & Dining - Restaurant and cafe recommendations
   3. Attractions & Activities - Sightseeing and things to do
   4. Accommodation - Hotels, hostels, and places to stay
   5. Transport & Getting Around - Local transportation options
   6. Local Tips & Culture - Cultural insights and local advice
   ```

3. **Source Coverage**: Set minimum number of sources to analyze

   ```
   Minimum: 5 sources (recommended: 15+)
   ```

### Process & Output

1. **Content Discovery**: The tool finds relevant Lemon8 posts based on your query
2. **Smart Analysis**: Each post is analyzed for:
   - Relevance to your query (scored 0-1.0)
   - Content value and authenticity
   - Practical travel information
3. **Progress Tracking**: Real-time updates on:
   - Sources analyzed
   - Relevant content found
   - Average relevance scores
4. **Guide Generation**: Creates a comprehensive Markdown guide with:
   - Detailed recommendations
   - Cost information
   - Transport options
   - Local tips and insights
   - Important travel notes
   - Visual content organization

All outputs are saved to the `output/` directory with the following structure:

```
output/
└── [run_id]_[timestamp]/        # e.g. cafes_in_johor_bahru_20250311_000816/
    ├── metadata/              # Analysis metadata and screenshots
    │   ├── *.md              # Content analysis files
    │   └── *.png             # Post screenshots
    └── posts/                # Processed post content
        └── *.md              # Individual analyzed posts
```

## 🛠️ Implementation Details

### Agent Architecture

The system uses CrewAI to orchestrate a team of specialized agents:

1. **Lemon8 Scraper Agent**

   - Handles content discovery and extraction
   - Captures post screenshots and metadata
   - Preserves image references and social metrics

2. **Relevance Checker Agent**

   - Scores content relevance (0-1.0)
   - Filters for travel-specific information
   - Validates source authenticity

3. **Content Analyzer Agent**

   - Extracts structured information
   - Processes using LangChain + OpenAI
   - Maintains original context and citations

4. **Report Aggregator Agent**
   - Combines multiple sources
   - Cross-validates information
   - Generates cohesive travel guides

### Analysis Pipeline

1. **Initial Processing**:

   - YAML frontmatter extraction
   - Image path normalization
   - Metadata preservation

2. **Content Analysis**:

   - Overview generation
   - Place/activity breakdown
   - Social metrics tracking
   - Screenshot integration

3. **Guide Compilation**:
   - Multi-source aggregation
   - Category organization
   - Local insights integration
   - Visual content mapping

### Model Configuration

- Uses OpenAI GPT models via LangChain
- Temperature: 0.7 (balanced creativity/accuracy)
- Includes structured prompts for consistent output
- Preserves original URLs and citations

## 🤝 Contributing

Contributions are welcome! Feel free to:

- Submit issues for bugs or feature requests
- Open pull requests with improvements
- Suggest new travel-related features
- Help improve guide generation

## 📝 License

MIT License - feel free to use this code in your own projects!
