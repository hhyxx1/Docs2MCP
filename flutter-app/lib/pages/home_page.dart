import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:docs2mcp_frontend/services/mcp_service.dart';

class HomePage extends StatefulWidget {
  @override
  _HomePageState createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final TextEditingController _urlController = TextEditingController();
  final TextEditingController _serverUrlController = TextEditingController();

  @override
  void initState() {
    super.initState();
    final provider = Provider.of<MCPProvider>(context, listen: false);
    _serverUrlController.text = provider.serverUrl;
    provider.fetchServerStatus();
    provider.fetchDocuments();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Docs2MCP'),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh),
            onPressed: () {
              Provider.of<MCPProvider>(context, listen: false).fetchServerStatus();
            },
          ),
        ],
      ),
      body: Consumer<MCPProvider>(
        builder: (context, provider, child) {
          return Padding(
            padding: const EdgeInsets.all(16.0),
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Server Configuration
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Server Configuration', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                          SizedBox(height: 10),
                          TextField(
                            controller: _serverUrlController,
                            decoration: InputDecoration(
                              labelText: 'Server URL',
                              border: OutlineInputBorder(),
                            ),
                          ),
                          SizedBox(height: 10),
                          ElevatedButton(
                            onPressed: () {
                              provider.serverUrl = _serverUrlController.text;
                            },
                            child: Text('Update Server URL'),
                          ),
                        ],
                      ),
                    ),
                  ),
                  SizedBox(height: 20),

                  // Server Status
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Server Status', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                          SizedBox(height: 10),
                          if (provider.isLoading) ...[
                            Center(child: CircularProgressIndicator()),
                          ] else if (provider.error.isNotEmpty) ...[
                            Text('Error: ${provider.error}', style: TextStyle(color: Colors.red)),
                          ] else ...[
                            Text('Status: ${provider.serverStatus['status'] ?? 'Unknown'}'),
                            Text('Version: ${provider.serverStatus['version'] ?? 'Unknown'}'),
                            Text('Crawlers: ${provider.serverStatus['crawlers'] ?? 0}'),
                          ],
                        ],
                      ),
                    ),
                  ),
                  SizedBox(height: 20),

                  // Add Document
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Add Document', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                          SizedBox(height: 10),
                          TextField(
                            controller: _urlController,
                            decoration: InputDecoration(
                              labelText: 'Document URL',
                              border: OutlineInputBorder(),
                              hintText: 'e.g., https://developer.huawei.com/consumer/cn/doc/',
                            ),
                          ),
                          SizedBox(height: 10),
                          ElevatedButton(
                            onPressed: provider.isLoading ? null : () {
                              if (_urlController.text.isNotEmpty) {
                                provider.addDocument(_urlController.text);
                              }
                            },
                            child: Text('Add Document'),
                          ),
                        ],
                      ),
                    ),
                  ),
                  SizedBox(height: 20),

                  // Documents List
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Documents', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                          SizedBox(height: 10),
                          if (provider.documents.isEmpty) ...[
                            Text('No documents added yet'),
                          ] else ...[
                            ListView.builder(
                              shrinkWrap: true,
                              itemCount: provider.documents.length,
                              itemBuilder: (context, index) {
                                final doc = provider.documents[index];
                                return ListTile(
                                  title: Text(doc['title'] ?? 'Untitled'),
                                  subtitle: Text(doc['url'] ?? ''),
                                );
                              },
                            ),
                          ],
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
