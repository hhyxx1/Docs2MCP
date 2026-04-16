from flask import Flask, request, jsonify
import os
import logging
from dotenv import load_dotenv
from utils.crawler import crawl_document, load_documents
from utils.scheduler import start_scheduler, init_watcher, get_watcher

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

documents = []
DATA_DIR = os.path.join(os.path.dirname(__file__), '../../data')

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
        use_selenium = data.get('use_selenium', False)
        result = crawl_document(url, use_selenium=use_selenium)

        watcher = get_watcher()
        if watcher:
            watcher.add_document(url)

        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        logger.error(f"Failed to crawl {url}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/docs/list', methods=['GET'])
def list_documents():
    docs = load_documents()
    return jsonify({'success': True, 'documents': docs, 'total': len(docs)}), 200

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
    docs = load_documents()
    resources = []
    for doc in docs:
        resources.append({
            'uri': f"docs://{doc.get('url', '').replace('://', '_').replace('/', '_')}",
            'name': doc.get('title', 'Untitled'),
            'description': f"Documentation: {doc.get('url', '')}"
        })
    return jsonify({'resources': resources}), 200

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

if __name__ == '__main__':
    os.makedirs(DATA_DIR, exist_ok=True)
    init_watcher(crawl_document, check_interval=3600)
    start_scheduler(crawl_document, check_interval=3600)

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
