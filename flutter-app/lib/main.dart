import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'pages/home_page.dart';
import 'services/mcp_service.dart';
import 'services/storage_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final storageService = StorageService();
  await storageService.init();
  
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => MCPProvider(storageService: storageService)),
        ChangeNotifierProvider.value(value: storageService),
      ],
      child: const Docs2MCPApp(),
    ),
  );
}

class Docs2MCPApp extends StatelessWidget {
  const Docs2MCPApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Docs2MCP',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
        appBarTheme: const AppBarTheme(
          centerTitle: true,
          elevation: 0,
        ),
        cardTheme: CardTheme(
          elevation: 2,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
        inputDecorationTheme: InputDecorationTheme(
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
          ),
          filled: true,
        ),
      ),
      home: const HomePage(),
    );
  }
}
