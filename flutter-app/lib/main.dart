import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:docs2mcp_frontend/pages/home_page.dart';
import 'package:docs2mcp_frontend/services/mcp_service.dart';

void main() {
  runApp(
    ChangeNotifierProvider(
      create: (context) => MCPProvider(),
      child: MyApp(),
    ),
  );
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Docs2MCP',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      home: HomePage(),
    );
  }
}
