import http.server
import socketserver
import json
import threading
import time
import requests
from bs4 import BeautifulSoup
import os
import concurrent.futures

PORT = 5000
documents = []
MAX_WORKERS = 4  # 限制并发线程数
REQUEST_TIMEOUT = 30  # 请求超时时间（秒）

# 创建线程池
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)

class MCPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/docs/add':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            url = data.get('url')
            
            if not url:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'URL is required'}).encode('utf-8'))
                return
            
            try:
                # 使用线程池处理爬取任务，避免阻塞主线程
                future = thread_pool.submit(crawl_document, url)
                result = future.result(timeout=REQUEST_TIMEOUT)
                documents.append(result)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'data': result}).encode('utf-8'))
            except concurrent.futures.TimeoutError:
                self.send_response(504)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Request timeout'}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_GET(self):
        if self.path == '/api/docs/list':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'documents': documents}).encode('utf-8'))
        elif self.path == '/api/server/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'running',
                'version': '1.0.0',
                'crawlers': len(documents)
            }).encode('utf-8'))
        elif self.path == '/api/ide/ai':
            # IDE中AI调用的接口
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            # 构建供AI使用的文档数据
            ai_data = {
                'documents': [
                    {
                        'url': doc['url'],
                        'title': doc['title'],
                        'content': '\n'.join([item['text'] for item in doc['content'] if item['text']]),
                        'timestamp': doc['timestamp']
                    }
                    for doc in documents
                ],
                'total_documents': len(documents)
            }
            self.wfile.write(json.dumps(ai_data).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

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
        save_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'data')
        os.makedirs(save_path, exist_ok=True)
        
        filename = url.replace('://', '_').replace('/', '_').replace('.', '_') + '.json'
        with open(os.path.join(save_path, filename), 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return result
    except Exception as e:
        raise Exception(f"Crawling failed: {str(e)}")

def check_document_updates():
    """定期检查文档更新"""
    print(f"Checking document updates at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    # 这里应该实现检查文档更新的逻辑
    pass

def scheduler_loop():
    """调度器循环"""
    while True:
        check_document_updates()
        time.sleep(24 * 60 * 60)

def start_server():
    """启动服务器"""
    # 启动调度器线程
    scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
    scheduler_thread.start()
    print("Scheduler started")
    
    # 启动HTTP服务器
    with socketserver.TCPServer(("0.0.0.0", PORT), MCPRequestHandler) as httpd:
        print(f"MCP Server running at http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == '__main__':
    start_server()
