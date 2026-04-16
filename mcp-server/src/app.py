from flask import Flask, request, jsonify
import os
import json
import logging
from dotenv import load_dotenv
from utils.crawler import (
    crawl_document, crawl_documentation, load_crawled_documents, get_crawled_projects
)
from utils.scheduler import start_scheduler, init_watcher, get_watcher
import threading

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

documents = []
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'data')

crawl_tasks = {}

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

@app.route('/api/docs/add', methods=['POST'])
def add_document():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400

    try:
        max_docs = data.get('max_docs', 50)
        max_depth = data.get('max_depth', 2)

        def crawl_task():
            try:
                result = crawl_documentation(url, max_docs=max_docs, max_depth=max_depth)
                crawl_tasks[url] = {'status': 'completed', 'result': result}
            except Exception as e:
                crawl_tasks[url] = {'status': 'failed', 'error': str(e)}

        crawl_tasks[url] = {'status': 'running'}
        thread = threading.Thread(target=crawl_task)
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'message': 'Crawl started',
            'task_id': url,
            'status': 'running'
        }), 200
    except Exception as e:
        logger.error(f"Failed to crawl {url}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/docs/crawl/<task_id>', methods=['GET'])
def get_crawl_status(task_id):
    task = crawl_tasks.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify({'task_id': task_id, **task}), 200

@app.route('/api/docs/list', methods=['GET'])
def list_documents():
    projects = get_crawled_projects()
    return jsonify({'success': True, 'projects': projects, 'total': len(projects)}), 200

@app.route('/api/docs/<project_filename>', methods=['GET'])
def get_project_documents(project_filename):
    filepath = os.path.join(DATA_DIR, project_filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'Project not found'}), 404
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify({'success': True, 'data': data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/docs/search', methods=['GET'])
def search_docs():
    query = request.args.get('q', '')
    project = request.args.get('project', '')
    if not query:
        return jsonify({'error': 'Query is required'}), 400

    projects = get_crawled_projects()
    results = []
    query_lower = query.lower()

    for proj in projects:
        if project and proj['filename'] != project:
            continue
        filepath = os.path.join(DATA_DIR, proj['filename'])
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for doc in data.get('documents', []):
                if query_lower in doc.get('title', '').lower() or query_lower in doc.get('content', '').lower():
                    results.append({
                        'title': doc.get('title', ''),
                        'url': doc.get('url', ''),
                        'project': proj['filename'],
                        'snippet': doc.get('content', '')[:300]
                    })
                    if len(results) >= 20:
                        break
        except Exception:
            continue

    return jsonify({'success': True, 'query': query, 'results': results, 'total': len(results)}), 200

@app.route('/api/docs/remove', methods=['POST'])
def remove_document():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400

    watcher = get_watcher()
    if watcher and watcher.remove_document(url):
        return jsonify({'success': True, 'message': 'Document removed'}), 200
    return jsonify({'error': 'Document not found'}), 404

@app.route('/api/docs/refresh', methods=['POST'])
def refresh_document():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400

    try:
        result = crawl_document(url)
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/server/status', methods=['GET'])
def server_status():
    watcher = get_watcher()
    doc_count = len(watcher.documents) if watcher else 0
    return jsonify({
        'status': 'running',
        'version': '1.0.0',
        'documents_monitored': doc_count,
        'uptime': 'N/A'
    }), 200

@app.route('/api/ide/query', methods=['GET', 'POST'])
def ide_query():
    if request.method == 'POST':
        data = request.json
        query = data.get('query', '')
    else:
        query = request.args.get('q', '')

    if not query:
        return jsonify({'error': 'Query is required'}), 400

    results = search_documents(query)
    return jsonify({
        'success': True,
        'query': query,
        'results': results,
        'total': len(results)
    }), 200

@app.route('/mcp/info', methods=['GET'])
def mcp_info():
    return jsonify({
        'name': 'Docs2MCP Server',
        'version': '1.0.0',
        'description': 'Documentation to MCP server for AI development assistance',
        'capabilities': {
            'document_crawl': True,
            'document_search': True,
            'realtime_updates': True,
            'ide_integration': True
        }
    }), 200

@app.route('/mcp/resources', methods=['GET'])
def mcp_resources():
    projects = get_crawled_projects()
    resources = []
    for proj in projects:
        filepath = os.path.join(DATA_DIR, proj['filename'])
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for doc in data.get('documents', []):
                resources.append({
                    'uri': f"docs://{doc.get('url', '').replace('://', '_').replace('/', '_')}",
                    'name': doc.get('title', 'Untitled'),
                    'description': doc.get('url', ''),
                    'project': proj['filename'],
                    'content': doc.get('content', '')[:500]
                })
        except Exception:
            continue
    return jsonify({'resources': resources, 'total': len(resources)}), 200

@app.route('/mcp/resources/<resource_uri>', methods=['GET'])
def mcp_get_resource(resource_uri):
    projects = get_crawled_projects()
    for proj in projects:
        filepath = os.path.join(DATA_DIR, proj['filename'])
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for doc in data.get('documents', []):
                uri = f"docs://{doc.get('url', '').replace('://', '_').replace('/', '_')}"
                if uri == resource_uri:
                    return jsonify({
                        'resource': {
                            'uri': uri,
                            'name': doc.get('title', 'Untitled'),
                            'content': doc.get('content', ''),
                            'url': doc.get('url', ''),
                            'project': proj['filename']
                        }
                    }), 200
        except Exception:
            continue
    return jsonify({'error': 'Resource not found'}), 404

@app.route('/mcp/tools', methods=['GET'])
def mcp_tools():
    tools = [
        {
            'name': 'search_documentation',
            'description': 'Search through crawled documentation',
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'query': {'type': 'string'},
                    'limit': {'type': 'number', 'default': 10}
                },
                'required': ['query']
            }
        },
        {
            'name': 'get_document',
            'description': 'Get full document by URL',
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'url': {'type': 'string'}
                },
                'required': ['url']
            }
        },
        {
            'name': 'crawl_document',
            'description': 'Add and crawl new documentation',
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'url': {'type': 'string'},
                    'use_selenium': {'type': 'boolean', 'default': False}
                },
                'required': ['url']
            }
        }
    ]
    return jsonify({'tools': tools}), 200

def search_documents(query, limit=10):
    """Search through loaded documents"""
    if not query:
        return []

    projects = get_crawled_projects()
    results = []
    query_lower = query.lower()

    for proj in projects:
        filepath = os.path.join(DATA_DIR, proj['filename'])
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for doc in data.get('documents', []):
                content = doc.get('content', '')
                title = doc.get('title', '')

                if query_lower in content.lower() or query_lower in title.lower():
                    content_lower = content.lower()
                    matches = []
                    start = 0
                    while True:
                        idx = content_lower.find(query_lower, start)
                        if idx == -1:
                            break
                        snippet_start = max(0, idx - 50)
                        snippet_end = min(len(content), idx + len(query) + 100)
                        snippet = content[snippet_start:snippet_end]
                        matches.append({
                            'type': 'text',
                            'snippet': snippet
                        })
                        start = idx + 1
                        if len(matches) >= 3:
                            break

                    results.append({
                        'url': doc.get('url'),
                        'title': title,
                        'project': proj['filename'],
                        'matches': matches,
                        'score': content_lower.count(query_lower)
                    })
        except Exception:
            continue

    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]

if __name__ == '__main__':
    os.makedirs(DATA_DIR, exist_ok=True)
    init_watcher(crawl_document, check_interval=3600)
    start_scheduler(crawl_document, check_interval=3600)

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
