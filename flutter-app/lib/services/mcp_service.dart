import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'storage_service.dart';

class MCPProvider extends ChangeNotifier {
  final StorageService _storageService;
  bool _isLoading = false;
  String _error = '';
  List<dynamic> _documents = [];
  Map<String, dynamic> _serverStatus = {};
  List<dynamic> _searchResults = [];

  MCPProvider({required StorageService storageService})
      : _storageService = storageService;

  String get serverUrl => _storageService.serverUrl;
  bool get isLoading => _isLoading;
  String get error => _error;
  List<dynamic> get documents => _documents;
  Map<String, dynamic> get serverStatus => _serverStatus;
  List<dynamic> get searchResults => _searchResults;

  Future<void> updateServerUrl(String url) async {
    await _storageService.setServerUrl(url);
    notifyListeners();
    await fetchServerStatus();
    await fetchDocuments();
  }

  Future<bool> _checkConnection() async {
    try {
      final response = await http
          .get(Uri.parse('$serverUrl/api/server/status'))
          .timeout(const Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  Future<void> addDocument(String url, {bool useSelenium = false}) async {
    _isLoading = true;
    _error = '';
    notifyListeners();

    try {
      final response = await http.post(
        Uri.parse('$serverUrl/api/docs/add'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'url': url,
          'use_selenium': useSelenium,
        }),
      ).timeout(const Duration(seconds: 60));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          await fetchDocuments();
        } else {
          _error = data['error'] ?? 'Failed to add document';
        }
      } else {
        _error = 'Server error: ${response.statusCode}';
      }
    } catch (e) {
      _error = 'Network error: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> removeDocument(String url) async {
    _isLoading = true;
    _error = '';
    notifyListeners();

    try {
      final response = await http.post(
        Uri.parse('$serverUrl/api/docs/remove'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'url': url}),
      ).timeout(const Duration(seconds: 30));

      if (response.statusCode == 200) {
        await fetchDocuments();
      } else {
        final data = jsonDecode(response.body);
        _error = data['error'] ?? 'Failed to remove document';
      }
    } catch (e) {
      _error = 'Network error: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> refreshDocument(String url) async {
    _isLoading = true;
    _error = '';
    notifyListeners();

    try {
      final response = await http.post(
        Uri.parse('$serverUrl/api/docs/refresh'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'url': url}),
      ).timeout(const Duration(seconds: 60));

      if (response.statusCode == 200) {
        await fetchDocuments();
      } else {
        final data = jsonDecode(response.body);
        _error = data['error'] ?? 'Failed to refresh document';
      }
    } catch (e) {
      _error = 'Network error: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> fetchDocuments() async {
    _isLoading = true;
    _error = '';
    notifyListeners();

    try {
      final response = await http
          .get(Uri.parse('$serverUrl/api/docs/list'))
          .timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _documents = data['projects'] ?? [];
      } else {
        _error = 'Server error: ${response.statusCode}';
      }
    } catch (e) {
      _error = 'Network error: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> fetchServerStatus() async {
    try {
      final response = await http
          .get(Uri.parse('$serverUrl/api/server/status'))
          .timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        _serverStatus = jsonDecode(response.body);
        _error = '';
      } else {
        _error = 'Server error: ${response.statusCode}';
      }
    } catch (e) {
      _error = 'Cannot connect to server: $e';
      _serverStatus = {'status': 'offline', 'error': '$e'};
    }
    notifyListeners();
  }

  Future<void> searchDocuments(String query) async {
    if (query.isEmpty) {
      _searchResults = [];
      notifyListeners();
      return;
    }

    _isLoading = true;
    _error = '';
    notifyListeners();

    try {
      final response = await http.get(
        Uri.parse('$serverUrl/api/ide/query?q=${Uri.encodeComponent(query)}'),
      ).timeout(const Duration(seconds: 30));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _searchResults = data['results'] ?? [];
      } else {
        _error = 'Search error: ${response.statusCode}';
      }
    } catch (e) {
      _error = 'Search error: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void clearError() {
    _error = '';
    notifyListeners();
  }
}
