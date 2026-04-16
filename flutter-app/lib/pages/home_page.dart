import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/mcp_service.dart';
import '../services/storage_service.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final TextEditingController _urlController = TextEditingController();
  final TextEditingController _serverUrlController = TextEditingController();
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final provider = Provider.of<MCPProvider>(context, listen: false);
      _serverUrlController.text = provider.serverUrl;
      _loadData();
    });
  }

  Future<void> _loadData() async {
    final provider = Provider.of<MCPProvider>(context, listen: false);
    await provider.fetchServerStatus();
    await provider.fetchDocuments();
  }

  @override
  void dispose() {
    _tabController.dispose();
    _urlController.dispose();
    _serverUrlController.dispose();
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Docs2MCP'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(icon: Icon(Icons.dashboard), text: 'Dashboard'),
            Tab(icon: Icon(Icons.add_circle), text: 'Add Doc'),
            Tab(icon: Icon(Icons.search), text: 'Search'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadData,
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: Consumer<MCPProvider>(
        builder: (context, provider, child) {
          if (provider.error.isNotEmpty) {
            WidgetsBinding.instance.addPostFrameCallback((_) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text(provider.error),
                  backgroundColor: Colors.red,
                  action: SnackBarAction(
                    label: 'Dismiss',
                    textColor: Colors.white,
                    onPressed: () => provider.clearError(),
                  ),
                ),
              );
              provider.clearError();
            });
          }

          return TabBarView(
            controller: _tabController,
            children: [
              _buildDashboardTab(provider),
              _buildAddDocTab(provider),
              _buildSearchTab(provider),
            ],
          );
        },
      ),
    );
  }

  Widget _buildDashboardTab(MCPProvider provider) {
    final status = provider.serverStatus;
    final isOnline = status['status'] == 'running';

    return RefreshIndicator(
      onRefresh: _loadData,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildStatusCard(status, isOnline),
            const SizedBox(height: 16),
            _buildServerConfigCard(provider),
            const SizedBox(height: 16),
            _buildDocumentsCard(provider),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusCard(Map<String, dynamic> status, bool isOnline) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  isOnline ? Icons.cloud_done : Icons.cloud_off,
                  color: isOnline ? Colors.green : Colors.red,
                  size: 32,
                ),
                const SizedBox(width: 12),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      isOnline ? 'Server Online' : 'Server Offline',
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      'Version: ${status['version'] ?? 'N/A'}',
                      style: TextStyle(color: Colors.grey[600]),
                    ),
                  ],
                ),
              ],
            ),
            const Divider(height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildStatusItem(
                  'Documents',
                  '${status['documents_monitored'] ?? 0}',
                  Icons.description,
                ),
                _buildStatusItem(
                  'Status',
                  isOnline ? 'Running' : 'Down',
                  isOnline ? Icons.check_circle : Icons.error,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusItem(String label, String value, IconData icon) {
    return Column(
      children: [
        Icon(icon, color: Colors.blue),
        const SizedBox(height: 4),
        Text(
          value,
          style: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: TextStyle(
            color: Colors.grey[600],
            fontSize: 12,
          ),
        ),
      ],
    );
  }

  Widget _buildServerConfigCard(MCPProvider provider) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.settings, size: 20),
                SizedBox(width: 8),
                Text(
                  'Server Configuration',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _serverUrlController,
              decoration: InputDecoration(
                labelText: 'Server URL',
                hintText: 'http://115.190.247.178:5000',
                prefixIcon: const Icon(Icons.link),
                suffixIcon: IconButton(
                  icon: const Icon(Icons.save),
                  onPressed: () async {
                    await provider.updateServerUrl(_serverUrlController.text);
                    if (mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Server URL updated')),
                      );
                    }
                  },
                ),
              ),
              onSubmitted: (value) async {
                await provider.updateServerUrl(value);
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDocumentsCard(MCPProvider provider) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Row(
                  children: [
                    Icon(Icons.folder_open, size: 20),
                    SizedBox(width: 8),
                    Text(
                      'Documents',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
                Text(
                  '${provider.documents.length} total',
                  style: TextStyle(color: Colors.grey[600]),
                ),
              ],
            ),
            const SizedBox(height: 12),
            if (provider.isLoading)
              const Center(child: CircularProgressIndicator())
            else if (provider.documents.isEmpty)
              const Center(
                child: Padding(
                  padding: EdgeInsets.all(24),
                  child: Column(
                    children: [
                      Icon(Icons.inbox, size: 48, color: Colors.grey),
                      SizedBox(height: 8),
                      Text('No documents added yet'),
                    ],
                  ),
                ),
              )
            else
              ListView.separated(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: provider.documents.length,
                separatorBuilder: (_, __) => const Divider(),
                itemBuilder: (context, index) {
                  final doc = provider.documents[index];
                  return ListTile(
                    leading: const Icon(Icons.article),
                    title: Text(
                      doc['title'] ?? 'Untitled',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    subtitle: Text(
                      doc['url'] ?? '',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 12),
                    ),
                    trailing: PopupMenuButton<String>(
                      onSelected: (value) async {
                        if (value == 'refresh') {
                          await provider.refreshDocument(doc['url']);
                        } else if (value == 'remove') {
                          await provider.removeDocument(doc['url']);
                        }
                      },
                      itemBuilder: (context) => [
                        const PopupMenuItem(
                          value: 'refresh',
                          child: Row(
                            children: [
                              Icon(Icons.refresh, size: 18),
                              SizedBox(width: 8),
                              Text('Refresh'),
                            ],
                          ),
                        ),
                        const PopupMenuItem(
                          value: 'remove',
                          child: Row(
                            children: [
                              Icon(Icons.delete, size: 18, color: Colors.red),
                              SizedBox(width: 8),
                              Text('Remove', style: TextStyle(color: Colors.red)),
                            ],
                          ),
                        ),
                      ],
                    ),
                  );
                },
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildAddDocTab(MCPProvider provider) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Card(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Add New Documentation',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  SizedBox(height: 8),
                  Text(
                    'Enter the URL of a documentation page to crawl and monitor for updates.',
                    style: TextStyle(color: Colors.grey),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  TextField(
                    controller: _urlController,
                    decoration: const InputDecoration(
                      labelText: 'Documentation URL',
                      hintText: 'https://developer.huawei.com/consumer/cn/doc/',
                      prefixIcon: Icon(Icons.link),
                    ),
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: provider.isLoading
                          ? null
                          : () async {
                              if (_urlController.text.isNotEmpty) {
                                await provider.addDocument(
                                  _urlController.text,
                                  useSelenium: true,
                                );
                                if (provider.error.isEmpty && mounted) {
                                  _urlController.clear();
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(
                                      content: Text('Document added successfully'),
                                      backgroundColor: Colors.green,
                                    ),
                                  );
                                  _tabController.animateTo(0);
                                }
                              }
                            },
                      icon: const Icon(Icons.add),
                      label: Text(
                        provider.isLoading
                            ? 'Adding...'
                            : 'Add Documentation',
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          const Card(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Quick Add Examples',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  SizedBox(height: 12),
                  _QuickAddTile(
                    title: 'Huawei HarmonyOS',
                    url: 'https://developer.huawei.com/consumer/cn/doc/',
                    icon: Icons.flutter_dash,
                  ),
                  _QuickAddTile(
                    title: 'Flutter',
                    url: 'https://docs.flutter.dev/',
                    icon: Icons.flutter_dash,
                  ),
                  _QuickAddTile(
                    title: 'Dart',
                    url: 'https://dart.dev/guides',
                    icon: Icons.code,
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSearchTab(MCPProvider provider) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(16),
          child: TextField(
            controller: _searchController,
            decoration: InputDecoration(
              hintText: 'Search documentation...',
              prefixIcon: const Icon(Icons.search),
              suffixIcon: IconButton(
                icon: const Icon(Icons.clear),
                onPressed: () {
                  _searchController.clear();
                  provider.searchDocuments('');
                },
              ),
            ),
            onSubmitted: (value) => provider.searchDocuments(value),
          ),
        ),
        Expanded(
          child: provider.isLoading
              ? const Center(child: CircularProgressIndicator())
              : provider.searchResults.isEmpty
                  ? const Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.search, size: 64, color: Colors.grey),
                          SizedBox(height: 16),
                          Text(
                            'Search for documentation content',
                            style: TextStyle(color: Colors.grey),
                          ),
                        ],
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      itemCount: provider.searchResults.length,
                      itemBuilder: (context, index) {
                        final result = provider.searchResults[index];
                        return Card(
                          margin: const EdgeInsets.only(bottom: 12),
                          child: ExpansionTile(
                            leading: const Icon(Icons.article),
                            title: Text(
                              result['title'] ?? 'Untitled',
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                            subtitle: Text(
                              result['url'] ?? '',
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(fontSize: 12),
                            ),
                            children: [
                              Padding(
                                padding: const EdgeInsets.all(16),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    for (final match in result['matches'] ?? [])
                                      Padding(
                                        padding: const EdgeInsets.only(bottom: 8),
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            Container(
                                              padding: const EdgeInsets.symmetric(
                                                horizontal: 8,
                                                vertical: 2,
                                              ),
                                              decoration: BoxDecoration(
                                                color: Colors.blue[100],
                                                borderRadius: BorderRadius.circular(4),
                                              ),
                                              child: Text(
                                                match['type']?.toUpperCase() ?? 'TEXT',
                                                style: TextStyle(
                                                  fontSize: 10,
                                                  color: Colors.blue[800],
                                                ),
                                              ),
                                            ),
                                            const SizedBox(height: 4),
                                            Text(match['snippet'] ?? ''),
                                          ],
                                        ),
                                      ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
        ),
      ],
    );
  }
}

class _QuickAddTile extends StatelessWidget {
  final String title;
  final String url;
  final IconData icon;

  const _QuickAddTile({
    required this.title,
    required this.url,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon),
      title: Text(title),
      subtitle: Text(url, style: const TextStyle(fontSize: 11)),
      trailing: IconButton(
        icon: const Icon(Icons.add_circle_outline),
        onPressed: () {
          context.read<MCPProvider>().addDocument(url, useSelenium: true);
        },
      ),
    );
  }
}
