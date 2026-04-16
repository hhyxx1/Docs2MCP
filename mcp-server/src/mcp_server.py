import json
import os
import sys
import threading
import time
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(__file__))

from utils.crawler import crawl_document, load_documents, crawl_with_requests
from utils.scheduler import start_scheduler, get_watcher, init_watcher

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

HOST = '0.0.0.0'
PORT = 5000
DATA_DIR = os.path.join(os.path.dirname(__file__), '../../data')
documents = []
MAX_WORKERS = 4

class MCPHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, format, *args):
        logger.info(f"{self.address_string()} - {format % args}")

    def send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == '/api/docs/list':
            docs = load_documents()
            self.send_json_response(200, {
                'success': True,
                'documents': docs,
                'total': len(docs)
            })

        elif parsed.path == '/api/server/status':
            watcher = get_watcher()
            doc_count = len(watcher.documents) if watcher else 0
            self.send_json_response(200, {
                'status': 'running',
                'version': '1.0.0',
                'uptime': time.time() - server_start_time,
                'documents_monitored': doc_count,
                'timestamp': datetime.now().isoformat()
            })

        elif parsed.path == '/api/ide/query':
            query = parse_qs(parsed.query).get('q', [''])[0]
            results = search_documents(query)
            self.send_json_response(200, {
                'success': True,
                'query': query,
                'results': results,
                'total': len(results)
            })

        elif parsed.path.startswith('/api/docs/'):
            doc_id = parsed.path.split('/')[-1]
            doc = get_document_by_id(doc_id)
            if doc:
                self.send_json_response(200, {'success': True, 'document': doc})
            else:
                self.send_json_response(404, {'error': 'Document not found'})

        elif parsed.path == '/mcp/info':
            self.send_json_response(200, {
                'name': 'Docs2MCP Server',
                'version': '1.0.0',
                'description': 'Documentation to MCP server for AI development assistance',
                'capabilities': {
                    'document_crawl': True,
                    'document_search': True,
                    'realtime_updates': True,
                    'ide_integration': True
                },
                'endpoints': {
                    'add_document': '/api/docs/add',
                    'list_documents': '/api/docs/list',
                    'search': '/api/ide/query',
                    'document': '/api/docs/<id>'
                }
            })

        elif parsed.path.startswith('/mcp/'):
            self.handle_mcp_request(parsed)

        else:
            self.send_json_response(404, {'error': 'Not found'})

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        try:
            data = json.loads(post_data.decode('utf-8'))
        except json.JSONDecodeError:
            self.send_json_response(400, {'error': 'Invalid JSON'})
            return

        if parsed.path == '/api/docs/add':
            url = data.get('url')
            if not url:
                self.send_json_response(400, {'error': 'URL is required'})
                return

            try:
                use_selenium = data.get('use_selenium', False)
                result = crawl_document(url, use_selenium=use_selenium)

                watcher = get_watcher()
                if watcher:
                    watcher.add_document(url)

                self.send_json_response(200, {
                    'success': True,
                    'data': result,
                    'message': 'Document crawled successfully'
                })
            except Exception as e:
                logger.error(f"Failed to crawl {url}: {e}")
                self.send_json_response(500, {'error': str(e)})

        elif parsed.path == '/api/docs/remove':
            url = data.get('url')
            if not url:
                self.send_json_response(400, {'error': 'URL is required'})
                return

            watcher = get_watcher()
            if watcher and watcher.remove_document(url):
                self.send_json_response(200, {
                    'success': True,
                    'message': 'Document removed from monitoring'
                })
            else:
                self.send_json_response(404, {'error': 'Document not found'})

        elif parsed.path == '/api/docs/refresh':
            url = data.get('url')
            if not url:
                self.send_json_response(400, {'error': 'URL is required'})
                return

            try:
                result = crawl_document(url)
                self.send_json_response(200, {
                    'success': True,
                    'data': result,
                    'message': 'Document refreshed successfully'
                })
            except Exception as e:
                self.send_json_response(500, {'error': str(e)})

        elif parsed.path == '/mcp/query':
            query = data.get('query', '')
            results = search_documents(query)
            self.send_json_response(200, {
                'success': True,
                'query': query,
                'results': results,
                'total': len(results)
            })

        else:
            self.send_json_response(404, {'error': 'Endpoint not found'})

    def handle_mcp_request(self, parsed):
        path_parts = parsed.path.split('/')

        if len(path_parts) >= 3:
            resource = path_parts[2]

            if resource == 'resources':
                resources = get_mcp_resources()
                self.send_json_response(200, {
                    'resources': resources
                })

            elif resource == 'tools':
                tools = get_mcp_tools()
                self.send_json_response(200, {
                    'tools': tools
                })

            elif resource == 'search':
                query = parse_qs(parsed.query).get('q', [''])[0]
                if not query:
                    body = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))).decode('utf-8'))
                    query = body.get('query', '')
                results = search_documents(query)
                self.send_json_response(200, {
                    'success': True,
                    'results': results
                })

            elif resource == 'call':
                self.send_json_response(200, {
                    'success': True,
                    'message': 'Tool calling endpoint - use POST with tool name and parameters'
                })

            else:
                self.send_json_response(404, {'error': 'MCP endpoint not found'})
        else:
            self.send_json_response(404, {'error': 'Invalid MCP path'})

def get_mcp_resources():
    """获取MCP资源列表"""
    docs = load_documents()
    resources = []

    for doc in docs:
        resources.append({
            'uri': f"docs://{doc.get('url', '').replace('://', '_').replace('/', '_')}",
            'name': doc.get('title', 'Untitled'),
            'description': f"Documentation: {doc.get('url', '')}",
            'mimeType': 'application/json'
        })

    return resources

def get_mcp_tools():
    """获取MCP工具列表"""
    return [
        {
            'name': 'search_documentation',
            'description': 'Search through crawled documentation for specific topics or keywords',
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'query': {
                        'type': 'string',
                        'description': 'Search query to find relevant documentation'
                    },
                    'limit': {
                        'type': 'number',
                        'description': 'Maximum number of results to return',
                        'default': 10
                    }
                },
                'required': ['query']
            }
        },
        {
            'name': 'get_document',
            'description': 'Get full document content by URL or ID',
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'url': {
                        'type': 'string',
                        'description': 'URL of the document to retrieve'
                    }
                },
                'required': ['url']
            }
        },
        {
            'name': 'crawl_document',
            'description': 'Add and crawl a new documentation URL',
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'url': {
                        'type': 'string',
                        'description': 'URL of the documentation to crawl'
                    },
                    'use_selenium': {
                        'type': 'boolean',
                        'description': 'Whether to use Selenium for dynamic content',
                        'default': False
                    }
                },
                'required': ['url']
            }
        }
    ]

def search_documents(query, limit=10):
    """搜索文档内容"""
    if not query:
        return []

    docs = load_documents()
    results = []
    query_lower = query.lower()

    for doc in docs:
        content_text = ' '.join([
            item.get('text', '') for item in doc.get('content', [])
        ]).lower()

        title_text = doc.get('title', '').lower()

        if query_lower in content_text or query_lower in title_text:
            matches = []
            for item in doc.get('content', []):
                if query_lower in item.get('text', '').lower():
                    matches.append({
                        'type': item.get('type'),
                        'text': item.get('text', ''),
                        'snippet': item.get('text', '')[:200]
                    })

            results.append({
                'url': doc.get('url'),
                'title': doc.get('title'),
                'matches': matches[:5],
                'crawled_at': doc.get('crawled_at'),
                'score': content_text.count(query_lower)
            })

    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]

def get_document_by_id(doc_id):
    """根据ID获取文档"""
    docs = load_documents()
    doc_id_decoded = doc_id.replace('_', '/').replace('-dot-', '.')
    for doc in docs:
        if doc.get('url') == doc_id_decoded:
            return doc
    for doc in docs:
        safe_id = doc.get('url', '').replace('://', '_').replace('/', '_').replace('.', '-dot-')
        if safe_id == doc_id:
            return doc
    return None

server_start_time = time.time()

def start_server():
    """启动MCP服务器"""
    global server_start_time
    server_start_time = time.time()

    os.makedirs(DATA_DIR, exist_ok=True)

    init_watcher(crawl_document, check_interval=3600)
    start_scheduler(crawl_document, check_interval=3600)

    server = HTTPServer((HOST, PORT), MCPHandler)
    logger.info(f"MCP Server running at http://{HOST}:{PORT}")
    logger.info(f"MCP endpoint: http://{HOST}:{PORT}/mcp/info")
    logger.info(f"IDE query endpoint: http://{HOST}:{PORT}/api/ide/query?q=<search>")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
        server.shutdown()

if __name__ == '__main__':
    start_server()
