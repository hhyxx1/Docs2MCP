import requests
from bs4 import BeautifulSoup
import json
import os
import re
import hashlib
from datetime import datetime

DOCUMENTS_DIR = os.path.join(os.path.dirname(__file__), '../../data')

def get_safe_filename(url):
    """将URL转换为安全的文件名"""
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    safe_name = re.sub(r'[^\w\-]', '_', url[:50])
    return f"{safe_name}_{url_hash}"

def crawl_document(url, depth=2, use_selenium=False):
    """爬取文档内容，支持深度爬取

    Args:
        url: 文档URL
        depth: 爬取深度，默认2层
        use_selenium: 是否使用Selenium处理动态内容
    """
    try:
        if use_selenium:
            return crawl_with_selenium(url, depth)
        else:
            return crawl_with_requests(url, depth)
    except Exception as e:
        raise Exception(f"Crawling failed: {str(e)}")

def crawl_with_requests(url, depth=2):
    """使用requests爬取文档内容（适用于静态页面）"""
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
    main_selectors = ['article', '.content', '.main-content', '#content', 'main', '.doc-content', '.article-content']

    for selector in main_selectors:
        main_content = soup.select_one(selector)
        if main_content:
            content = extract_content_elements(main_content)
            break

    if not content:
        content = extract_content_elements(soup.body() if soup.body else soup)

    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('/') or href.startswith(url):
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
        'status': 'success'
    }

    save_document(url, result)
    return result

def crawl_with_selenium(url, depth=2):
    """使用Selenium爬取文档内容（适用于动态页面）"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.action_chains import ActionChains
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

        expand_shadow_elements(driver)

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        title = soup.title.string if soup.title else 'Untitled Document'

        content = []
        main_selectors = ['article', '.content', '.main-content', '#content', 'main', '.doc-content']
        for selector in main_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                content = extract_content_elements(main_content)
                break

        if not content:
            content = extract_content_elements(soup.body() if soup.body else soup)

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

def expand_shadow_elements(driver):
    """展开Shadow DOM元素和折叠菜单"""
    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time

        expandable_elements = driver.find_elements(By.CSS_SELECTOR,
            '[class*="expand"], [class*="toggle"], [class*="collapse"], '
            '[aria-expanded="false"], [data-toggle], .more, .expand')
        
        for elem in expandable_elements[:20]:
            try:
                if elem.is_displayed():
                    driver.execute_script("arguments[0].click();", elem)
                    time.sleep(0.5)
            except:
                pass
    except Exception:
        pass

def extract_content_elements(element):
    """提取内容元素"""
    content = []
    if not element:
        return content

    try:
        if hasattr(element, 'find_all'):
            elements = element.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'pre', 'code', 'tr', 'th', 'td'])
            for tag in elements:
                if hasattr(tag, 'get_text'):
                    text = tag.get_text(strip=True)
                    if text and len(text) > 3:
                        classes = tag.get('class', [])
                        if isinstance(classes, list):
                            class_str = ' '.join(classes)
                        else:
                            class_str = str(classes)
                        content.append({
                            'type': tag.name if hasattr(tag, 'name') else 'unknown',
                            'text': text,
                            'class': class_str
                        })
    except Exception as e:
        print(f"Error extracting content: {e}")

    return content

def is_valid_doc_url(url):
    """检查URL是否是有效的文档URL"""
    if not url or url.startswith('#') or url.startswith('javascript:'):
        return False
    url_lower = url.lower()
    skip_patterns = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.css', '.js', 
                     '微博', 'twitter', 'facebook', 'github.com/login']
    for pattern in skip_patterns:
        if pattern in url_lower:
            return False
    return True

def save_document(url, result):
    """保存文档到文件系统"""
    os.makedirs(DOCUMENTS_DIR, exist_ok=True)
    filename = get_safe_filename(url) + '.json'
    filepath = os.path.join(DOCUMENTS_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

def load_documents():
    """加载所有已保存的文档"""
    documents = []
    if not os.path.exists(DOCUMENTS_DIR):
        return documents
    
    for filename in os.listdir(DOCUMENTS_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(DOCUMENTS_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    documents.append(json.load(f))
            except Exception:
                pass
    return documents

def check_for_updates(doc_url, existing_content_hash=None):
    """检查文档是否有更新"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'If-Modified-Since': existing_content_hash
        }
        response = requests.get(doc_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            current_hash = hashlib.md5(response.content).hexdigest()
            if current_hash != existing_content_hash:
                return True, current_hash
        return False, existing_content_hash
    except Exception:
        return False, existing_content_hash
