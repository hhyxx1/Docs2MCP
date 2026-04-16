import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

class StorageService extends ChangeNotifier {
  static const String _serverUrlKey = 'server_url';
  static const String _defaultServerUrl = 'http://115.190.247.178:5000';
  
  late SharedPreferences _prefs;
  String _serverUrl = _defaultServerUrl;

  String get serverUrl => _serverUrl;

  Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
    _serverUrl = _prefs.getString(_serverUrlKey) ?? _defaultServerUrl;
    notifyListeners();
  }

  Future<void> setServerUrl(String url) async {
    _serverUrl = url;
    await _prefs.setString(_serverUrlKey, url);
    notifyListeners();
  }
}
