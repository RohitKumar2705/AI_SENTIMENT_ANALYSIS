# news article collection from news and rss feeds

import os
import sys
import requests
from bs4 import BeautifulSoup
from typing import List,Dict,Any
import xml.etree.ElementTree as ET

if __package__ is None or __package__ == "":
    # Allow running this file directly: python AI_AGENTS/data_collector/news_data.py
    ai_agents_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if ai_agents_dir not in sys.path:
        sys.path.insert(0, ai_agents_dir)
    from config import RSS_FEEDS, MAX_ARTICLES_PER_CATEGORY, HEADERS
else:
    from ..config import RSS_FEEDS, MAX_ARTICLES_PER_CATEGORY, HEADERS


def get_news_articles() -> List[Dict[str,Any]]:
    """
    Fetch recent news articles from Google News RSS feeds.
    
    Returns:
        List of article dictionaries containing:
        - category: 'Economy' or 'Politics'
        - title: Article headline
        - source: Publisher name (CNN, Reuters, etc.)
        - description: Article summary/snippet
        - link: Article URL (Google News redirect)
        - pub_date: Publication date string
        - content: Combined source + description text
    """
    articles = []

    print("fetching news articles...\n")

    for category, feed_url in RSS_FEEDS.items():
        try:
            print(f"Fetching {category} news...")
            response = requests.get(feed_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            
            try:
                root = ET.fromstring(response.content)
            except Exception as e:
                print(f"  [ERROR] Could not parse XML feed: {str(e)[:50]}")
                continue

            # RSS: channel/item. Atom: entry
            items = root.findall('.//item')
            if not items:
                items = root.findall('.//{http://www.w3.org/2005/Atom}entry')
            items = items[:MAX_ARTICLES_PER_CATEGORY]

            print(f"  Found {len(items)} entries in {category} feed")

            for item in items:
                try:
                    title = 'No title'
                    title_tag = item.find('title')
                    if title_tag is None:
                        title_tag = item.find('{http://www.w3.org/2005/Atom}title')
                    if title_tag is not None and title_tag.text:
                        title = title_tag.text.strip()

                    link = None
                    link_tag = item.find('link')
                    if link_tag is not None:
                        link = (link_tag.text or '').strip() or link_tag.get('href')

                    if not link:
                        atom_link_tag = item.find('{http://www.w3.org/2005/Atom}link')
                        if atom_link_tag is not None:
                            link = atom_link_tag.get('href')

                    pub_date = 'Unknown date'
                    pub_tag = item.find('pubDate')
                    if pub_tag is None:
                        pub_tag = item.find('{http://www.w3.org/2005/Atom}updated')
                    if pub_tag is not None and pub_tag.text:
                        pub_date = pub_tag.text.strip()
                    
                    # Extract source (publisher)
                    source = ''
                    source_tag = item.find('source')
                    if source_tag is not None and source_tag.text:
                        source = source_tag.text.strip()
                    
                    # Extract description/summary
                    description = ''
                    desc_tag = item.find('description')
                    if desc_tag is None:
                        desc_tag = item.find('{http://www.w3.org/2005/Atom}summary')
                    if desc_tag is not None and desc_tag.text:
                        desc_soup = BeautifulSoup(desc_tag.text, 'html.parser')
                        description = desc_soup.get_text(strip=True)
                    
                    # Build content from RSS data
                    content_parts = []
                    if source:
                        content_parts.append(f"Source: {source}.")
                    if description:
                        content_parts.append(description)
                    
                    content = ' '.join(content_parts) if content_parts else title
                    
                    if link:
                        article = {
                            'category': category,
                            'title': title,
                            'source': source,
                            'description': description,
                            'content': content,
                            'link': link,
                            'pub_date': pub_date,
                            'scraped': False
                        }
                        articles.append(article)
                        print(f"  [OK] {title[:70]}...")
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"  [ERROR] Error fetching {category} news: {str(e)[:50]}")
    
    print(f"\n[OK] Found {len(articles)} articles total")
    return articles


if __name__ == "__main__":
    data = get_news_articles()
    print(f"Fetched {len(data)} articles.")