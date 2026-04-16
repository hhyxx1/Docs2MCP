import requests
from bs4 import BeautifulSoup
import json
import os
import re
import hashlib
from datetime import datetime
import traceback

DOCUMENTS_DIR = os.path.join(os.path.dirname(__file__), '../../data')

def get_safe_filename(url):
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    safe_name = re.sub(r'[^\w\-]', '_', url[:50])
    return f"{safe_name}_{url_hash}"

def crawl_document(url, depth=2, use_selenium=False):
    try:
        if use_selenium:
            return crawl_with_selenium(url, depth)
        else:
            return crawl_with_requests(url, depth)
    except Exception as e:
        raise Exception(f"Crawling failed: {str(e)}")

def crawl_with_requests(url, depth=2):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or 'utf-8'

    soup = BeautifulSoup(response.content, 'html.parser')

    title = soup.title.string if soup.title else 'Untitled Document'

    content = []
    main_selectors = [
        'article', '.content', '.main-content', '#content', 'main',
        '.doc-content', '.article-content', '.container', '.wrapper',
        '[class*="content"]', '[class*="main"]', '[class*="doc"]'
    ]

    for selector in main_selectors:
        try:
            main_content = soup.select_one(selector)
            if main_content and hasattr(main_content, 'find_all'):
                content = extract_content_elements(main_content)
                if content:
                    break
        except Exception:
            continue

    if not content:
        try:
            body = soup.body if soup.body else soup
            content = extract_content_elements(body)
        except Exception:
            content = []

    links = []
    for a in soup.find_all('a', href=True):
        try:
            href = a['href']
            if href.startswith('/') or href.startswith(url):
                full_url = requests.compat.urljoin(url, href)
                if is_valid_doc_url(full_url):
                    links.append({
                        'text': a.get_text(strip=True) or '链接',
                        'href': full_url
                    })
        except Exception:
            continue

    result = {
        'url': url,
        'title': title,
        'content': content,
        'links': links[:50],
        'timestamp': datetime.now().isoformat(),
        'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'success'
    }

    save_document(url, result)
    return result

def crawl_with_selenium(url, depth=2):
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
    except ImportError:
        raise Exception("Selenium not installed. Run: pip install selenium")

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(60)
        driver.get(url)

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        import time
        time.sleep(3)

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        title = soup.title.string if soup.title else 'Untitled Document'

        content = []
        for selector in ['article', '.content', 'main', '#content']:
            main_content = soup.select_one(selector)
            if main_content:
                content = extract_content_elements(main_content)
                break

        if not content:
            content = extract_content_elements(soup.body())

        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = requests.compat.urljoin(url, href)
            if is_valid_doc_url(full_url):
                links.append({
                    'text': a.get_text(strip=True) or '链接',
                    'href': full_url
                })

        result = {
            'url': url,
            'title': title,
            'content': content,
            'links': links[:50],
            'timestamp': datetime.now().isoformat(),
            'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'crawl_method': 'selenium',
            'status': 'success'
        }

        save_document(url, result)
        return result

    finally:
        if driver:
            driver.quit()

def extract_content_elements(element):
    content = []
    if not element:
        return content

    try:
        if not hasattr(element, 'find_all'):
            return content

        selectors = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'pre', 'code', 'tr', 'th', 'td', 'div', 'span']
        elements = element.find_all(selectors)

        for tag in elements:
            try:
                if not hasattr(tag, 'get_text'):
                    continue
                text = tag.get_text(strip=True)
                if text and len(text) > 5:
                    tag_name = tag.name if hasattr(tag, 'name') else 'unknown'
                    classes = tag.get('class', [])
                    if isinstance(classes, list):
                        class_str = ' '.join(classes)
                    else:
                        class_str = str(classes) if classes else ''

                    content.append({
                        'type': tag_name,
                        'text': text[:500],
                        'class': class_str
                    })
            except Exception:
                continue
    except Exception as e:
        print(f"Error extracting content: {e}")

    return content

def is_valid_doc_url(url):
    if not url or url.startswith('#') or url.startswith('javascript:'):
        return False
    url_lower = url.lower()
    skip_patterns = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.css', '.js',
                     '微博', 'twitter', 'facebook', 'github.com/login', 'javascript:']
    for pattern in skip_patterns:
        if pattern in url_lower:
            return False
    return True

def save_document(url, result):
    os.makedirs(DOCUMENTS_DIR, exist_ok=True)
    filename = get_safe_filename(url) + '.json'
    filepath = os.path.join(DOCUMENTS_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

def load_documents():
    documents = []
    if not os.path.exists(DOCUMENTS_DIR):
        return documents

    for filename in os.listdir(DOCUMENTS_DIR):
        if filename.endswith('.json') and not filename.startswith('document_registry'):
            filepath = os.path.join(DOCUMENTS_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    doc = json.load(f)
                    if 'url' in doc and 'status' in doc:
                        documents.append(doc)
            except Exception:
                pass
    return documents

def check_for_updates(doc_url, existing_content_hash=None):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        response = requests.get(doc_url, headers=headers, timeout=10)

        if response.status_code == 200:
            current_hash = hashlib.md5(response.content).hexdigest()
            if current_hash != existing_content_hash:
                return True, current_hash
        return False, existing_content_hash
    except Exception:
        return False, existing_content_hash
