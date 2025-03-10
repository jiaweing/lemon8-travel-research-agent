from typing import List, Dict, Set
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
        
        # Initialize the batch prompt template
        self.batch_prompt = PromptTemplate(
            input_variables=["reports", "query", "current_data"],
            template="""Analyze these reports about {query} and integrate new information.

CURRENT STATUS:
{current_data}

NEW REPORTS TO ANALYZE:
{reports}

PROVIDE UPDATES IN THIS FORMAT:

## 🏷️ Place Updates
### [Place Name]
![Representative Image](image_path) (if available from reports)
Total Mentions: [X]
Rating: [Y]/5.0

Key Features:
- [Feature 1]
- [Feature 2]

Visual Highlights:
- Image 1: [Description] (image_path)
- Image 2: [Description] (image_path)

Sources: [list]

## 💰 Cost Information
### [Category]
- [Item/Service]: [Price Range] ([X] mentions)
_Verified prices from [month/year]_

## 🚇 Location & Access
### [Area/Route]
New Options:
- [Option] ([X] recommends)
Tips:
- [Tip] ([Y] confirms)

## 💡 Tips & Recommendations
### [Category]
- [Tip] ([X] people)
Consensus: [High/Medium/Low]

## ⚠️ Important Updates
Priority: [High/Medium/Low]
- [Warning]
Impact: [Description]
Duration: [If temporary]

## 📊 Statistics
Areas: [area] (+[X] mentions)
Highlights: [item] (+[Y] mentions)
Patterns: [observation]
Popular Times: [timing trend]

Include source counts and cross-validate information."""
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

    def _parse_photos(self, section: str) -> List[tuple]:
        """Parse photo section into structured data"""
        photos = []
        current_photo = {}
        
        for line in section.split('\n'):
            if line.startswith('!['):
                description = line[2:line.index(']')]
                url = line[line.index('(')+1:line.index(')')]
                current_photo = {'description': description, 'url': url}
            elif line.startswith('Type:'):
                current_photo['type'] = line.split(':', 1)[1].strip()
            elif line.startswith('Quality:'):
                current_photo['quality'] = int(line.split(':', 1)[1].strip().split('/')[0])
            elif line.startswith('_Source:'):
                current_photo['source'] = line[8:-1].strip()
                if all(k in current_photo for k in ['description', 'url', 'type', 'quality', 'source']):
                    photos.append((
                        current_photo['description'],
                        current_photo['url'],
                        current_photo['source'],
                        current_photo['type'],
                        current_photo['quality']
                    ))
                current_photo = {}
                
        return photos

    def _parse_markdown_sections(self, content: str) -> Dict[str, str]:
        """Parse markdown content into sections"""
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            if line.startswith('## '):
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                current_section = line[3:].strip()
                current_content = []
            elif current_section:
                current_content.append(line)
                
        if current_section:
            sections[current_section] = '\n'.join(current_content)
            
        return sections

    def _merge_place_details(self, existing: Dict, new: Dict) -> None:
        """Merge new place details with existing data"""
        existing['mentions'] += new['mentions']
        existing['ratings'].extend(new['ratings'])
        existing['features'].update(new['features'])
        existing['sources'].extend(s for s in new['sources'] if s not in existing['sources'])

    def _parse_places(self, section: str) -> Dict[str, Dict]:
        """Parse places section into structured data"""
        places = {}
        current_place = None
        current_data = {}
        
        for line in section.split('\n'):
            if line.startswith('### '):
                if current_place and current_data:
                    places[current_place] = current_data
                current_place = line[4:].strip()
                current_data = {
                    'mentions': 0,
                    'ratings': [],
                    'features': set(),
                    'sources': [],
                    'images': []  # Add images to store
                }
            elif current_place:
                if 'Total Mentions:' in line:
                    current_data['mentions'] = int(line.split(':')[1].strip())
                elif 'Rating:' in line:
                    rating = float(line.split(':')[1].split('/')[0].strip())
                    current_data['ratings'].append(rating)
                elif line.strip().startswith('- ') and 'Sources:' not in line:
                    current_data['features'].add(line.strip()[2:])
                elif 'Sources:' in line:
                    current_data['sources'].extend([s.strip() for s in line.split(':')[1].strip().split(',')])
                    
        if current_place and current_data:
            places[current_place] = current_data
            
        return places

    def _format_place_section(self, name: str, details: Dict) -> str:
        """Format a place section with details and stats"""
        rating = sum(details["ratings"])/len(details["ratings"]) if details["ratings"] else None
        sections = [
            f"\n### {name}",
            f"Recommended by {details['mentions']} people",
            f"Rating: {'%.1f/5.0' % rating if rating else 'No ratings'}"
        ]
        
        if details["features"]:
            sections.extend([
                "\nHighlights:",
                *[f"- {feature}" for feature in details["features"]]
            ])
            
        if len(details["sources"]) > 0:
            sections.append(f"\n_Verified by {len(details['sources'])} sources_")
            
        return "\n".join(sections)

    def _format_photo(self, photo: tuple) -> str:
        """Format a photo with metadata"""
        description, url, source, type_, quality = photo
        return f"\n### {type_}\n![{description}]({url})\n_Source: {source}_"

    def _format_cost_section(self, category: str, items: List) -> str:
        """Format a cost section with price ranges"""
        sections = [
            f"\n### {category}",
            *[f"- {item}: {price_range} ({mentions} mentions)"
              for item, price_range, _, mentions in items]
        ]
        return "\n".join(sections)

    def _format_transport(self, area: str, details: Dict) -> str:
        """Format transport information for an area"""
        sections = [
            f"\n### {area}",
            "\nOptions:",
            *[f"- {option}" for option, _ in sorted(details['options'], 
                                                  key=lambda x: x[1], 
                                                  reverse=True)],
            "\nTips:",
            *[f"- {tip}" for tip, _ in sorted(details['tips'], 
                                             key=lambda x: x[1], 
                                             reverse=True)],
            f"\n_Information from {len(details['sources'])} sources_"
        ]
        return "\n".join(sections)

    def _format_tips_section(self, category: str, tips_list: List) -> str:
        """Format tips with consensus information"""
        sections = [
            f"\n### {category}",
            *[f"- {tip} ({sources} people mention this) - {consensus} consensus"
              for tip, sources, consensus in sorted(tips_list, 
                                                  key=lambda x: x[1], 
                                                  reverse=True)]
        ]
        return "\n".join(sections)

    def _format_warning(self, warning: tuple) -> str:
        """Format warning with priority and impact"""
        text, impact, sources, priority = warning
        priority_emoji = "🚨" if priority == "High" else "⚠️"
        return f"\n### {priority_emoji} {text}\n{impact}\n_Reported by {len(sources)} sources_"

    def _format_top_mentions(self, places: Dict, count: int) -> str:
        """Format top mentioned places summary"""
        top = sorted(
            [(name, details["mentions"]) for name, details in places.items()],
            key=lambda x: x[1],
            reverse=True
        )[:count]
        return "\n".join(f"- {name}: {mentions} mentions" for name, mentions in top)

    def _format_recent_stats(self, stats: Dict) -> str:
        """Format recent statistics summary"""
        sections = []
        if stats["areas"]:
            sections.append("Popular Areas: " + 
                          ", ".join(f"{area} ({count})" for area, count 
                                  in sorted(stats["areas"].items(), 
                                          key=lambda x: x[1], 
                                          reverse=True)[:3]))
        if stats["activities"]:
            sections.append("Top Activities: " + 
                          ", ".join(f"{act} ({count})" for act, count 
                                  in sorted(stats["activities"].items(), 
                                          key=lambda x: x[1], 
                                          reverse=True)[:3]))
        return "\n".join(sections)

    async def _analyze_batch(self, query: str, current_data: str, batch_content: str) -> str:
        """Analyze a batch of reports and return structured updates"""
        try:
            # Format and send prompt
            formatted_prompt = self.batch_prompt.format(
                query=query,
                current_data=current_data,
                reports=batch_content
            )
            
            response = self.llm.invoke(formatted_prompt)
            if not hasattr(response, 'content'):
                logger.error("❌ Batch analysis failed")
                return None
                
            return response.content
            
        except Exception as e:
            logger.error(f"❌ Batch analysis failed: {str(e)}")
            return None

    def _update_data(self, sections: Dict[str, str], photos: List, 
                    places: Dict, costs: Dict, transport: Dict, 
                    tips: Dict, warnings: List, stats: Dict) -> None:
        """Update aggregated data with new information from batch analysis"""
        # Update photos
        if "📸 New Photos" in sections:
            new_photos = self._parse_photos(sections["📸 New Photos"])
            for photo in new_photos:
                if photo not in photos:
                    photos.append(photo)
        
        # Update places
        if "🏷️ Place Updates" in sections:
            new_places = self._parse_places(sections["🏷️ Place Updates"])
            for name, details in new_places.items():
                if name not in places:
                    places[name] = details
                else:
                    self._merge_place_details(places[name], details)
        
        # Update costs
        if "💰 Cost Information" in sections:
            for line in sections["💰 Cost Information"].split('\n'):
                if line.startswith('### '):
                    current_category = line[4:].strip()
                    costs.setdefault(current_category, [])
                elif line.strip().startswith('- '):
                    try:
                        item_info = line[2:].strip()
                        item, rest = item_info.split(':', 1)
                        price_range = rest[:rest.rfind('(')].strip()
                        mentions = int(rest[rest.rfind('(')+1:rest.rfind(')')].split()[0])
                        costs[current_category].append((
                            item.strip(),
                            price_range,
                            datetime.now().strftime('%Y-%m'),
                            mentions
                        ))
                    except Exception as e:
                        logger.warning(f"Failed to parse cost line: {line} - {str(e)}")
        
        # Update transport
        if "🚇 Location & Access" in sections:
            current_area = None
            for line in sections["🚇 Location & Access"].split('\n'):
                if line.startswith('### '):
                    current_area = line[4:].strip()
                    transport.setdefault(current_area, {
                        'options': [],
                        'tips': [],
                        'sources': set()
                    })
                elif line.strip().startswith('- '):
                    item = line[2:line.rfind('(')].strip()
                    mentions = int(line[line.rfind('(')+1:line.rfind(')')].split()[0])
                    if 'New Options:' in sections["🚇 Location & Access"].split(line)[0]:
                        transport[current_area]['options'].append((item, mentions))
                    elif 'Tips:' in sections["🚇 Location & Access"].split(line)[0]:
                        transport[current_area]['tips'].append((item, mentions))
        
        # Update tips
        if "💡 Tips & Recommendations" in sections:
            current_category = None
            for line in sections["💡 Tips & Recommendations"].split('\n'):
                if line.startswith('### '):
                    current_category = line[4:].strip()
                    tips.setdefault(current_category, [])
                elif line.strip().startswith('- '):
                    try:
                        tip = line[2:line.rfind('(')].strip()
                        mentions = int(line[line.rfind('(')+1:line.rfind(')')].split()[0])
                        consensus = line[line.rfind('Consensus:')+10:].strip()
                        
                        existing_tip = next((t for t, s, c in tips[current_category] if t == tip), None)
                        if existing_tip:
                            idx = next(i for i, (t, s, c) in enumerate(tips[current_category]) if t == tip)
                            _, sources, _ = tips[current_category][idx]
                            tips[current_category][idx] = (tip, sources + mentions, consensus)
                        else:
                            tips[current_category].append((tip, mentions, consensus))
                    except Exception as e:
                        logger.warning(f"Failed to parse tip line: {line} - {str(e)}")
        
        # Update warnings
        if "⚠️ Important Updates" in sections:
            current_warning = None
            current_priority = None
            current_impact = None
            
            for line in sections["⚠️ Important Updates"].split('\n'):
                if line.startswith('Priority:'):
                    current_priority = line.split(':', 1)[1].strip()
                elif line.strip().startswith('- '):
                    current_warning = line[2:].strip()
                elif line.startswith('Impact:'):
                    current_impact = line.split(':', 1)[1].strip()
                    if current_warning and current_priority and current_impact:
                        if not any(w[0] == current_warning for w in warnings):
                            warnings.append((
                                current_warning,
                                current_impact,
                                set([datetime.now().strftime('%Y-%m')]),
                                current_priority
                            ))
                        current_warning = current_impact = None
        
        # Update statistics
        if "📊 Statistics" in sections:
            for line in sections["📊 Statistics"].split('\n'):
                try:
                    if line.startswith('Areas:'):
                        area, mentions = line.split(':', 1)[1].strip().split('(+')
                        mentions = int(mentions.rstrip(')'))
                        stats["areas"][area.strip()] = stats["areas"].get(area.strip(), 0) + mentions
                    elif line.startswith('Highlights:'):
                        activity, mentions = line.split(':', 1)[1].strip().split('(+')
                        mentions = int(mentions.rstrip(')'))
                        stats["activities"][activity.strip()] = stats["activities"].get(activity.strip(), 0) + mentions
                    elif line.startswith('Patterns:'):
                        pattern = line.split(':', 1)[1].strip()
                        stats["budget_patterns"][pattern] = stats["budget_patterns"].get(pattern, 0) + 1
                    elif line.startswith('Popular Times:'):
                        timing = line.split(':', 1)[1].strip()
                        stats["timing"][timing] = stats["timing"].get(timing, 0) + 1
                except Exception as e:
                    logger.warning(f"Failed to parse statistics line: {line} - {str(e)}")

    async def generate_final_report(self, query: str) -> str:
        """Generate a final consolidated report for the query"""
        logger.info(f"📊 Starting report generation for: {query}")
        
        # Load reports in batches
        report_batches = self._load_reports()
        
        # Initialize aggregated data structures
        photos = []  # [(description, url, source, type, quality)]
        places = {}  # name -> {mentions, ratings, features, sources}
        costs = {}   # category -> [(item, range, sources, mentions)]
        transport = {}  # area -> {options: [], tips: [], sources}
        tips = {}    # category -> [(tip, sources, consensus)]
        warnings = []  # [(text, impact, sources, priority)]
        stats = {
            "areas": {},
            "activities": {},
            "budget_patterns": {},
            "timing": {},
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Sanitize query for filename
        safe_query = "".join(c if c.isalnum() or c in " -_" else "_" for c in query)
        safe_query = safe_query.replace(" ", "_")[:100]
        final_report_path = os.path.join(self.output_dir, f"{safe_query}.md")
        
        try:
            # Process each batch
            for i, batch in enumerate(report_batches, 1):
                logger.info(f"🔄 Processing batch {i} of {len(report_batches)}")
                
                current_data = f"""
Current Progress:
- {len(photos)} photos collected
- {len(places)} places documented
- {len(costs)} price categories
- {len(transport)} areas with access info
- {len(tips)} recommendations
- {len(warnings)} important notes

Most Mentioned:
{self._format_top_mentions(places, 3)}

Recent Updates:
{self._format_recent_stats(stats)}"""
                
                batch_content = "\n\n---\n\n".join(
                    f"Report {j+1}:\n{report['content']}"
                    for j, report in enumerate(batch)
                )
                
                response = await self._analyze_batch(query, current_data, batch_content)
                if not response:
                    continue
                    
                sections = self._parse_markdown_sections(response)
                self._update_data(sections, photos, places, costs, transport, tips, warnings, stats)
            
            # Generate final report
            report_sections = [
                f"# {query}",  # Use original query as title
                "\n## 📍 Overview",
                f"Based on {sum(len(batch) for batch in report_batches)} verified sources",
                
                "\n## ⭐ Top Highlights",
                *[self._format_place_section(name, details) 
                  for name, details in sorted(
                      places.items(),
                      key=lambda x: (x[1]["mentions"], 
                                   sum(x[1]["ratings"])/len(x[1]["ratings"]) if x[1]["ratings"] else 0),
                      reverse=True
                  )[:10]],
                
                "\n## 📸 Photos",
                *[self._format_photo((desc, url, src, type_, qual)) 
                  for desc, url, src, type_, qual in sorted(photos, key=lambda x: x[4], reverse=True)[:15]],
                
                "\n## 💰 Costs",
                *[self._format_cost_section(category, items) 
                  for category, items in sorted(costs.items())],
                
                "\n## 🚇 Getting There & Around",
                *[self._format_transport(area, details) 
                  for area, details in sorted(transport.items())],
                
                "\n## 💡 Tips & Recommendations",
                *[self._format_tips_section(category, tip_list) 
                  for category, tip_list in sorted(tips.items())],
                
                "\n## ⚠️ Important Notes",
                *[self._format_warning(w) for w in sorted(warnings, key=lambda x: x[3], reverse=True)],
                
                f"\n## 📅 Last Updated",
                f"_{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_",
                f"\nBased on {sum(len(batch) for batch in report_batches)} verified sources"
            ]
            
            # Save final report
            with open(final_report_path, "w", encoding="utf-8") as f:
                f.write("\n".join(report_sections))
            
            logger.info(f"✅ Report completed at {final_report_path}")
            return final_report_path
            
        except Exception as e:
            error_msg = f"Report generation failed: {str(e)}"
            logger.error(error_msg)
            return error_msg
