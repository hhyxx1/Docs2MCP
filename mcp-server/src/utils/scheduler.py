import sched
import time
import os
import threading
import json
import hashlib
from datetime import datetime, timedelta

scheduler = sched.scheduler(time.time, time.sleep)
DATA_DIR = os.path.join(os.path.dirname(__file__), '../../data')

class DocumentWatcher:
    def __init__(self, crawl_func, check_interval=3600):
        self.crawl_func = crawl_func
        self.check_interval = check_interval
        self.documents = []
        self.doc_hashes = {}
        self._running = False
        self._thread = None

    def load_document_registry(self):
        """从注册表加载文档列表"""
        registry_path = os.path.join(DATA_DIR, 'document_registry.json')
        if os.path.exists(registry_path):
            try:
                with open(registry_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.documents = data.get('documents', [])
                    self.doc_hashes = data.get('hashes', {})
            except Exception as e:
                print(f"Failed to load registry: {e}")

    def save_document_registry(self):
        """保存文档注册表"""
        registry_path = os.path.join(DATA_DIR, 'document_registry.json')
        os.makedirs(DATA_DIR, exist_ok=True)
        try:
            with open(registry_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'documents': self.documents,
                    'hashes': self.doc_hashes,
                    'last_updated': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save registry: {e}")

    def add_document(self, url):
        """添加文档到监控列表"""
        if url not in self.documents:
            self.documents.append(url)
            self.save_document_registry()
            return True
        return False

    def remove_document(self, url):
        """从监控列表移除文档"""
        if url in self.documents:
            self.documents.remove(url)
            if url in self.doc_hashes:
                del self.doc_hashes[url]
            self.save_document_registry()
            return True
        return False

    def check_document_updates(self):
        """检查所有文档的更新"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking {len(self.documents)} documents for updates...")
        updated_docs = []

        for doc_url in self.documents[:]:
            try:
                result = self.crawl_func(doc_url)
                if result:
                    content_hash = hashlib.md5(
                        json.dumps(result.get('content', []), sort_keys=True).encode()
                    ).hexdigest()

                    if doc_url not in self.doc_hashes or self.doc_hashes[doc_url] != content_hash:
                        old_hash = self.doc_hashes.get(doc_url, 'unknown')
                        self.doc_hashes[doc_url] = content_hash
                        updated_docs.append({
                            'url': doc_url,
                            'title': result.get('title', 'Unknown'),
                            'old_hash': old_hash,
                            'new_hash': content_hash,
                            'updated_at': datetime.now().isoformat()
                        })
                        print(f"  [UPDATED] {doc_url}")

            except Exception as e:
                print(f"  [ERROR] Failed to check {doc_url}: {e}")

        if updated_docs:
            self.save_document_registry()
            self.save_update_log(updated_docs)

        print(f"Update check completed. {len(updated_docs)} documents updated.")
        return updated_docs

    def save_update_log(self, updates):
        """保存更新日志"""
        log_path = os.path.join(DATA_DIR, 'update_log.json')
        try:
            if os.path.exists(log_path):
                with open(log_path, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
        except Exception:
            logs = []

        logs.extend([{
            'timestamp': datetime.now().isoformat(),
            **update
        } for update in updates])

        logs = logs[-100:]

        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

    def start(self):
        """启动文档监控"""
        self._running = True
        self.load_document_registry()
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
        print(f"Document watcher started. Monitoring {len(self.documents)} documents.")

    def stop(self):
        """停止文档监控"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("Document watcher stopped.")

    def _watch_loop(self):
        """监控循环"""
        while self._running:
            self.check_document_updates()
            for _ in range(self.check_interval):
                if not self._running:
                    break
                time.sleep(1)

_watcher = None

def get_watcher():
    """获取全局文档监控器实例"""
    global _watcher
    return _watcher

def init_watcher(crawl_func, check_interval=3600):
    """初始化文档监控器"""
    global _watcher
    _watcher = DocumentWatcher(crawl_func, check_interval)
    return _watcher

def start_scheduler(crawl_func=None, check_interval=3600):
    """启动调度器"""
    global _watcher
    if _watcher is None and crawl_func:
        _watcher = DocumentWatcher(crawl_func, check_interval)
    if _watcher:
        _watcher.start()
    return _watcher

def shutdown_scheduler():
    """关闭调度器"""
    global _watcher
    if _watcher:
        _watcher.stop()

def check_document_updates():
    """定期检查文档更新"""
    global _watcher
    if _watcher:
        return _watcher.check_document_updates()
    return []

def _scheduler_loop():
    """调度器循环"""
    while True:
        check_document_updates()
        time.sleep(24 * 60 * 60)

def start_scheduler_thread():
    """启动调度器线程"""
    thread = threading.Thread(target=_scheduler_loop, daemon=True)
    thread.start()
    print("Scheduler thread started")
