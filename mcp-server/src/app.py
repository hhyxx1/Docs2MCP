from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from utils.crawler import crawl_document
from utils.scheduler import start_scheduler

load_dotenv()

app = Flask(__name__)

@app.route('/api/docs/add', methods=['POST'])
def add_document():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    try:
        result = crawl_document(url)
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/docs/list', methods=['GET'])
def list_documents():
    # 这里应该从数据库或文件系统中读取文档列表
    # 暂时返回模拟数据
    return jsonify({'documents': []}), 200

@app.route('/api/server/status', methods=['GET'])
def server_status():
    return jsonify({
        'status': 'running',
        'version': '1.0.0',
        'crawlers': 0
    }), 200

if __name__ == '__main__':
    start_scheduler()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
