import requests
from bs4 import BeautifulSoup
import json
import os

def crawl_document(url):
    """爬取文档内容"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 提取文档标题
        title = soup.title.string if soup.title else 'Untitled Document'
        
        # 提取正文内容
        content = []
        # 尝试不同的正文选择器
        selectors = ['article', '.content', '.main-content', '#content', 'main']
        for selector in selectors:
            main_content = soup.select_one(selector)
            if main_content:
                for paragraph in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'pre', 'code']):
                    content.append({
                        'type': paragraph.name,
                        'text': paragraph.get_text(strip=True)
                    })
                break
        
        # 如果没有找到正文，使用整个页面
        if not content:
            for paragraph in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'pre', 'code']):
                content.append({
                    'type': paragraph.name,
                    'text': paragraph.get_text(strip=True)
                })
        
        # 提取链接
        links = []
        for a in soup.find_all('a', href=True):
            links.append({
                'text': a.get_text(strip=True),
                'href': a['href']
            })
        
        result = {
            'url': url,
            'title': title,
            'content': content,
            'links': links,
            'timestamp': response.headers.get('Date', '')
        }
        
        # 保存爬取结果
        save_path = os.path.join(os.path.dirname(__file__), '../../data')
        os.makedirs(save_path, exist_ok=True)
        
        filename = url.replace('://', '_').replace('/', '_').replace('.', '_') + '.json'
        with open(os.path.join(save_path, filename), 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return result
    except Exception as e:
        raise Exception(f"Crawling failed: {str(e)}")
