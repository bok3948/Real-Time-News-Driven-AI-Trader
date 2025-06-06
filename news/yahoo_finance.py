import requests
from bs4 import BeautifulSoup
from typing import Tuple, List, Dict, Set, Optional
from .news_structure import Article
from .registry import register_crawler

def get_article_content(article_url: str, headers: Dict[str, str]) -> Tuple[str, str]:
    """
    Extracts content and publication time from a Yahoo Finance article.
    
    Args:
        article_url: The URL of the article to extract content from.
        headers: HTTP headers to use when making the request.
        
    Returns:
        A tuple containing the article content and publication time.
    """
    try:
        response = requests.get(article_url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        time_tag = soup.find('time')
        article_time = time_tag['datetime'] if time_tag and time_tag.has_attr('datetime') else "Time not found"

        content_container = soup.select_one('div.caas-body')
        if content_container:
            paragraphs = content_container.find_all('p')
            content = "\n".join([p.get_text(strip=True) for p in paragraphs])
            return content, article_time

        article_tag = soup.find('article')
        if article_tag:
            paragraphs = article_tag.find_all('p')
            content = "\n".join([p.get_text(strip=True) for p in paragraphs])
            return content, article_time

        canvas_content = soup.select_one('#Col1-0-ContentCanvas') 
        if canvas_content:
            paragraphs = canvas_content.find_all('p')
            if paragraphs:
                content = "\n".join([p.get_text(strip=True) for p in paragraphs])
                return content, article_time

        return "Content not found (selector update needed).", article_time
    except requests.exceptions.RequestException as e:
        print(f"Error fetching article content from {article_url}: {e}")
        return "Error occurred while fetching article content.", "Time not found"
    except Exception as e:
        print(f"An unexpected error occurred in get_article_content for {article_url}: {e}")
        return "Unexpected error occurred while processing article content.", "Time not found"

@register_crawler("yahoo_finance")
def crawl_yahoo_finance_news() -> Article:
    """
    Crawls Yahoo Finance latest news page and returns the most recent article.
    
    Returns:
        An Article object containing the most recent news article from Yahoo Finance.
        If no news is found, returns an empty Article with source="Yahoo Finance".
    """
    
    url = "https://finance.yahoo.com/topic/latest-news/"

    news_list = []
    processed_links = set()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news list from {url}: {e}")
        return None # Return empty list on failure

    soup = BeautifulSoup(response.content, 'html.parser')
    
    articles_elements = []
    article_source_type = None

    # Selector 1: New structure observed (a.titles-link with h2 child)
    selected_new_structure = soup.select('a.titles-link[href*="/news/"]')
    if selected_new_structure:
        articles_elements = selected_new_structure
        article_source_type = "new_structure_a_tag_with_h2_child"
    
    # Selector 2: Common stream item structure (li.stream-item h3 a)
    if not articles_elements:
        selected_li_stream = soup.select('li.stream-item h3 a[href*="/news/"]')
        if selected_li_stream:
            articles_elements = selected_li_stream
            article_source_type = "direct_a_tag_text"

    # Selector 3: Mega locator structure (div[data-test-locator="mega"] h3 a)
    if not articles_elements:
        selected_mega_locator = soup.select('div[data-test-locator="mega"] h3 a[href*="/news/"]')
        if selected_mega_locator:
            articles_elements = selected_mega_locator
            article_source_type = "direct_a_tag_text"

    # Selector 4: General links with aria-label (a[href*="/news/"][aria-label])
    if not articles_elements:
        selected_aria_label = soup.select('a[href*="/news/"][aria-label]')
        if selected_aria_label:
            articles_elements = selected_aria_label
            article_source_type = "direct_a_tag_text"
    
    # Selector 5: Fallback to any link that seems like a news article link
    if not articles_elements:
        selected_fallback = soup.select('a[href*="/news/"]') # More generic
        if selected_fallback:
            articles_elements = selected_fallback
            article_source_type = "fallback_a_tag" 


    for article_link_tag in articles_elements:
        title = None
        link = article_link_tag.get('href')

        if not link or not link.startswith(('/', 'http')):
            continue
        if not "/news/" in link and not "/video/" in link:
            continue

        if article_source_type == "new_structure_a_tag_with_h2_child":
            title_h2_tag = article_link_tag.select_one('h2')
            if title_h2_tag:
                title = title_h2_tag.get_text(strip=True)
        elif article_source_type == "direct_a_tag_text":
            if article_link_tag.has_attr('aria-label') and article_link_tag['aria-label']:
                title = article_link_tag['aria-label']
            else:
                title = article_link_tag.get_text(strip=True)
        elif article_source_type == "fallback_a_tag": 
            title = article_link_tag.get_text(strip=True)
            if not title or len(title) < 10:
                inner_title_element = article_link_tag.find(['h1', 'h2', 'h3', 'h4', 'div', 'span'], class_=lambda x: x != 'card-time-row' if x else True)
                if inner_title_element:
                    title = inner_title_element.get_text(strip=True)
        if not title:
            title = article_link_tag.get_text(strip=True)
            if not title:
                continue
        if title and link:
            if link.startswith('/'):
                link = 'https://finance.yahoo.com' + link
            if link not in processed_links:
                article_content, article_time = get_article_content(link, headers)
                if "Content not found" not in article_content and "Error occurred" not in article_content and "Unexpected error" not in article_content:
                    news_list.append({
                        'title': title,
                        'link': link,
                        'content': article_content,
                        'time': article_time
                    })
                    processed_links.add(link)
                else:
                    print(f"Skipping article due to content retrieval issue: {title}")
    
    if news_list:
        first_news = news_list[0]
        return Article(
            title=first_news['title'],
            url=first_news['link'],
            date=first_news['time'],
            content=first_news['content'],
            source="Yahoo Finance"
        )
    else:
        return None
