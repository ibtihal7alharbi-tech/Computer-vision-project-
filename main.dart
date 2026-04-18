import 'package:flutter/material.dart';
import 'screens/splash_screen.dart';

void main() {
  runApp(const MahdApp());
}

class MahdApp extends StatelessWidget {
  const MahdApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Mahd',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        scaffoldBackgroundColor: const Color(0xFFF5F0E8),
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF6B7F5E),
        ),
        fontFamily: 'SF Pro Display',
      ),
      home: const SplashScreen(),
    );
  }
}