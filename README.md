# 🌎 Lemon8 Travel Guide Generator

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![crawl4ai](https://img.shields.io/badge/crawl4ai-0.5.0-green.svg)](https://pypi.org/project/crawl4ai/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

An intelligent tool that generates comprehensive travel guides by analyzing authentic user experiences from Lemon8. Get real recommendations, local insights, and practical travel information based on crowdsourced content.

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
│   └── main.py                       # CLI interface
├── content/                          # Scraped content
├── reports/                          # Generated travel guides
└── requirements.txt                  # Python dependencies
```

## 💡 Usage Examples

### Generate a Travel Guide

```bash
python src/main.py

# Example queries:
# - things to do in london
# - best restaurants in tokyo
# - hidden gems in paris
# - local food in bangkok
```

### Content Types

The tool supports generating guides focused on specific aspects of travel:

1. **Everything** - Comprehensive destination guide
2. **Food & Dining** - Restaurant and cafe recommendations
3. **Attractions & Activities** - Sightseeing and things to do
4. **Accommodation** - Hotels, hostels, and places to stay
5. **Transport & Getting Around** - Local transportation options
6. **Local Tips & Culture** - Cultural insights and local advice

### Example Guide Structure

```markdown
# 🌎 Travel Guide: London

## 🎯 Quick Overview

Key information about the destination

## 📸 Travel Photos

Organized by category (food, attractions, etc.)

## 🗺️ Location & Access

Area information and getting there

## 💰 Cost Guide

Price ranges and budgeting information

## 🎯 Key Recommendations

Detailed place recommendations with:

- Location details
- Operating hours
- Cost information
- Must-try/see items
- Practical tips

## 🌟 Experiences & Activities

Activity categories and details

## 🎒 Travel Tips

- Local insights
- Cultural notes
- Practical advice

## ⚠️ Important Notes

Warnings and considerations
```

## 💻 Implementation Details

### Travel Content Analysis

- **Smart Relevance Checking**: Evaluates content based on:

  - Geographic relevance
  - Travel value
  - Content categories
  - Practical details
  - Source authenticity

- **Comprehensive Analysis**: Extracts:
  - Location information
  - Cost data
  - Operating hours
  - Transport options
  - Local tips
  - Cultural insights

### Guide Generation

- Aggregates information from multiple sources
- Cross-validates recommendations
- Organizes content by category
- Provides practical, actionable information
- Includes authentic photos and visuals

## 🔍 Supported Regions

- 🇸🇬 Singapore
- 🇲🇾 Malaysia
- 🇮🇩 Indonesia
- 🇹🇭 Thailand
- 🇻🇳 Vietnam
- 🇵🇭 Philippines

## 🤝 Contributing

Contributions are welcome! Feel free to:

- Submit issues for bugs or feature requests
- Open pull requests with improvements
- Suggest new travel-related features
- Help improve guide generation
- Add support for new regions

## 📝 License

MIT License - feel free to use this code in your own projects!
