import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

class MCPProvider extends ChangeNotifier {
  String _serverUrl = 'http://localhost:5000';
  bool _isLoading = false;
  String _error = '';
  List<dynamic> _documents = [];
  Map<String, dynamic> _serverStatus = {};

  String get serverUrl => _serverUrl;
  bool get isLoading => _isLoading;
  String get error => _error;
  List<dynamic> get documents => _documents;
  Map<String, dynamic> get serverStatus => _serverStatus;

  set serverUrl(String url) {
    _serverUrl = url;
    notifyListeners();
  }

  Future<void> addDocument(String url) async {
    _isLoading = true;
    _error = '';
    notifyListeners();

    try {
      final response = await http.post(
        Uri.parse('$_serverUrl/api/docs/add'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'url': url}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success']) {
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

  Future<void> fetchDocuments() async {
    _isLoading = true;
    _error = '';
    notifyListeners();

    try {
      final response = await http.get(Uri.parse('$_serverUrl/api/docs/list'));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _documents = data['documents'] ?? [];
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
    _isLoading = true;
    _error = '';
    notifyListeners();

    try {
      final response = await http.get(Uri.parse('$_serverUrl/api/server/status'));

      if (response.statusCode == 200) {
        _serverStatus = jsonDecode(response.body);
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
}
