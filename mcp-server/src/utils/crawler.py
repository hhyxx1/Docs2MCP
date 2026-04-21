import requests
from bs4 import BeautifulSoup
import json
import os
import re
import hashlib
from datetime import datetime
from urllib.parse import urljoin, urlparse
import traceback
from typing import List, Dict, Set, Optional

DOCUMENTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'data')

class DocumentationCrawler:
    def __init__(self, base_url: str, max_depth: int = 2, max_docs: int = 50):
        self.base_url = base_url
        self.max_depth = max_depth
        self.max_docs = max_docs
        self.visited_urls: Set[str] = set()
        self.documents: List[Dict] = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

    def is_valid_doc_url(self, url: str) -> bool:
        if not url or url.startswith('#') or url.startswith('javascript:') or url.startswith('mailto:'):
            return False
        parsed = urlparse(url)
        if parsed.fragment or not parsed.scheme:
            return False
        skip_patterns = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.css', '.js', '/static/']
        for pattern in skip_patterns:
            if pattern in url.lower():
                return False
        return True

    def extract_links_from_page(self, soup: BeautifulSoup, current_url: str) -> List[Dict]:
        links = []
        baseparsed = urlparse(current_url)
        for a in soup.find_all('a', href=True):
            try:
                href = a['href']
                full_url = urljoin(current_url, href)
                parsed = urlparse(full_url)

                if parsed.scheme not in ['http', 'https']:
                    continue
                if not self.is_valid_doc_url(full_url):
                    continue

                text = a.get_text(strip=True)
                if not text or len(text) < 3:
                    continue

                if baseparsed.netloc == parsed.netloc:
                    links.append({'text': text, 'href': full_url})
            except Exception:
                continue
        return links

    def extract_content_from_page(self, soup: BeautifulSoup, url: str) -> Dict:
        result = {
            'url': url,
            'title': '',
            'content': '',
            'content_html': '',
            'headings': [],
            'code_blocks': [],
            'links': [],
            'metadata': {}
        }

        result['title'] = soup.title.string if soup.title else 'Untitled'
        if isinstance(result['title'], bytes):
            result['title'] = result['title'].decode('utf-8', errors='replace')

        main_content = None
        content_selectors = [
            'article',
            '[role="main"]',
            'main',
            '.content',
            '.docs-content',
            '.documentation',
            '#content',
            '.markdown-body',
            '.article-content',
            '.post-content',
            '.doc-content'
        ]

        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content and len(main_content.get_text(strip=True)) > 200:
                break

        if not main_content:
            main_content = soup.body if soup.body else soup

        for tag in main_content.find_all(['h1', 'h2', 'h3', 'h4']):
            text = tag.get_text(strip=True)
            if text:
                result['headings'].append({
                    'level': int(tag.name[1]),
                    'text': text
                })

        for tag in main_content.find_all(['pre', 'code']):
            text = tag.get_text(strip=True)
            if text and len(text) > 10:
                lang = ''
                if tag.name == 'pre':
                    code_class = tag.get('class', [])
                    for c in code_class:
                        if c.startswith('language-'):
                            lang = c.replace('language-', '')
                            break
                result['code_blocks'].append({
                    'language': lang,
                    'code': text[:1000]
                })

        paragraphs = []
        for element in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote', 'pre']):
            text = element.get_text(strip=True)
            if text and len(text) > 10:
                tag_name = element.name
                if tag_name == 'li':
                    text = '• ' + text
                elif tag_name.startswith('h'):
                    text = '\n## ' + text + '\n'
                elif tag_name == 'blockquote':
                    text = '> ' + text
                elif tag_name == 'pre':
                    text = '\n```\n' + text + '\n```\n'
                paragraphs.append(text)

        result['content'] = '\n\n'.join(paragraphs)
        result['content_html'] = str(main_content)

        nav_links = self.extract_links_from_page(main_content, url)
        result['links'] = [{'text': l['text'], 'href': l['href']} for l in nav_links[:30]]

        return result

    def extract_toc_from_index(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        links = []
        parsed_base = urlparse(base_url)

        link_sources = []

        nav_selectors = ['nav', 'aside', '.sidebar', '#sidebar', '.navigation', '[role="navigation"]', 'ul.nav', 'ol.nav']
        for sel in nav_selectors:
            nav = soup.select_one(sel)
            if nav:
                link_sources.append(('nav', nav))

        article = soup.find('article')
        if article:
            link_sources.append(('article', article))

        main_content = None
        for sel in ['main', '[role="main"]', '.content', '.docs-content', '.documentation']:
            main = soup.select_one(sel)
            if main:
                main_content = main
                break

        if main_content:
            link_sources.append(('main', main_content))

        if not link_sources:
            link_sources.append(('body', soup.body if soup.body else soup))

        for source_name, source in link_sources:
            for a in source.find_all('a', href=True):
                try:
                    href = a['href']
                    full_url = urljoin(base_url, href)
                    parsed = urlparse(full_url)

                    if parsed.scheme not in ['http', 'https']:
                        continue
                    if parsed.netloc != parsed_base.netloc:
                        continue
                    if not self.is_valid_doc_url(full_url):
                        continue

                    text = a.get_text(strip=True)
                    if not text or len(text) < 3:
                        continue

                    path = parsed.path.lower()
                    skip_paths = ['/blog/', '/community/', '/versions', '/download/', '/changelog', '/newsletter', '/poll']
                    if any(p in path for p in skip_paths):
                        continue

                    links.append({'text': text, 'href': full_url})
                except Exception:
                    continue

        seen = set()
        unique_links = []
        for link in links:
            if link['href'] not in seen:
                seen.add(link['href'])
                unique_links.append(link)

        return unique_links

    def crawl_page(self, url: str, depth: int = 0) -> Optional[Dict]:
        if url in self.visited_urls:
            return None
        if depth > self.max_depth:
            return None
        if len(self.documents) >= self.max_docs:
            return None

        self.visited_urls.add(url)

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or 'utf-8'
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        if depth == 0:
            doc_links = self.extract_toc_from_index(soup, url)
            print(f"Found {len(doc_links)} document links from index page")

            for link in doc_links[:self.max_docs]:
                if len(self.documents) >= self.max_docs:
                    break
                self.crawl_page(link['href'], depth + 1)
        else:
            content = self.extract_content_from_page(soup, url)
            if content and len(content.get('content', '')) > 100:
                self.documents.append(content)
                print(f"Crawled: {content['title'][:60]}... ({len(self.documents)}/{self.max_docs})")

        return None

    def crawl(self) -> List[Dict]:
        print(f"Starting crawl of {self.base_url}")
        self.crawl_page(self.base_url, depth=0)
        print(f"Crawl complete! Total documents: {len(self.documents)}")
        return self.documents

def crawl_documentation(url: str, max_docs: int = 50, max_depth: int = 2) -> Dict:
    crawler = DocumentationCrawler(url, max_depth=max_depth, max_docs=max_docs)
    documents = crawler.crawl()

    os.makedirs(DOCUMENTS_DIR, exist_ok=True)
    safe_name = re.sub(r'[^\w\-]', '_', urlparse(url).netloc + urlparse(url).path)[:50]
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    filename = f"{safe_name}_{url_hash}"
    filepath = os.path.join(DOCUMENTS_DIR, filename + '.json')

    result = {
        'source_url': url,
        'crawled_at': datetime.now().isoformat(),
        'total_documents': len(documents),
        'documents': documents
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(documents)} documents to {filepath}")
    return result

def crawl_document(url: str, depth: int = 2, use_selenium: bool = False) -> Dict:
    crawler = DocumentationCrawler(url, max_depth=depth, max_docs=50)
    documents = crawler.crawl()
    return {
        'url': url,
        'title': documents[0]['title'] if documents else 'No content',
        'content': documents,
        'total': len(documents),
        'timestamp': datetime.now().isoformat(),
        'status': 'success'
    }

def load_crawled_documents():
    documents = []
    if not os.path.exists(DOCUMENTS_DIR):
        return documents

    for filename in os.listdir(DOCUMENTS_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(DOCUMENTS_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'documents' in data:
                        for doc in data['documents']:
                            doc['source_file'] = filename
                            documents.append(doc)
                    elif 'url' in data:
                        data['source_file'] = filename
                        documents.append(data)
            except Exception:
                pass
    return documents

def get_crawled_projects():
    projects = []
    if not os.path.exists(DOCUMENTS_DIR):
        return projects

    for filename in os.listdir(DOCUMENTS_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(DOCUMENTS_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    projects.append({
                        'source_url': data.get('source_url', 'Unknown'),
                        'crawled_at': data.get('crawled_at', ''),
                        'total_documents': data.get('total_documents', 0),
                        'filename': filename
                    })
            except Exception:
                pass
    return projects