import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/services.dart';
import 'dart:async';
import 'dart:typed_data';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../services/notification_service.dart';
import 'profile_screen.dart';
import 'reports_screen.dart';
import 'notifications_screen.dart';
import 'settings_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF7F3EE),
      body: IndexedStack(
        index: _currentIndex,
        children: const [_HomeContent(), ReportsScreen(), NotificationsScreen(), ProfileScreen()],
      ),
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          border: Border(top: BorderSide(color: Color(0xFFEEEEEE), width: 1)),
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          onTap: (index) => setState(() => _currentIndex = index),
          backgroundColor: Colors.transparent,
          elevation: 0,
          selectedItemColor: const Color(0xFF6B7F5E),
          unselectedItemColor: const Color(0xFFCCCCCC),
          type: BottomNavigationBarType.fixed,
          selectedLabelStyle: const TextStyle(fontWeight: FontWeight.w600, fontSize: 11),
          unselectedLabelStyle: const TextStyle(fontSize: 11),
          items: const [
            BottomNavigationBarItem(icon: Icon(Icons.home_rounded, size: 26), label: 'Home'),
            BottomNavigationBarItem(icon: Icon(Icons.insert_chart_outlined_rounded, size: 26), label: 'Reports'),
            BottomNavigationBarItem(icon: Icon(Icons.notifications_outlined, size: 26), label: 'Alerts'),
            BottomNavigationBarItem(icon: Icon(Icons.person_outline_rounded, size: 26), label: 'Profile'),
          ],
        ),
      ),
    );
  }
}

class _HomeContent extends StatefulWidget {
  const _HomeContent();
  @override
  State<_HomeContent> createState() => _HomeContentState();
}

class _HomeContentState extends State<_HomeContent> {
  late VideoPlayerController _videoController;
  String _status = '';
  bool _showAlert = false;
  bool _alertSent = false;
  bool _notificationSent = false; // only one notification ever
  Timer? _analysisTimer;
  int _stomachSeconds = 0;
  String _emergencyPhone = '';
  static const String baseUrl = 'http://127.0.0.1:8000/api';

  @override
  void initState() {
    super.initState();
    _loadEmergencyPhone();
    _initVideo();
  }

  Future<void> _loadEmergencyPhone() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() => _emergencyPhone = prefs.getString('emergencyPhone') ?? '911');
  }

  void _initVideo() {
    _videoController = VideoPlayerController.asset('assets/test_baby.mp4')
      ..initialize().then((_) {
        setState(() {});
        _videoController.setLooping(true);
        _videoController.play();
        _startAnalysis();
      });
  }

  void _startAnalysis() {
    _analysisTimer?.cancel();
    _analysisTimer = Timer.periodic(const Duration(seconds: 3), (_) async {
      if (_showAlert) return;
      await _analyzeCurrentFrame();
    });
  }

  Future<void> _analyzeCurrentFrame() async {
    try {
      final ByteData data = await rootBundle.load('assets/test_baby.mp4');
      final Uint8List videoBytes = data.buffer.asUint8List();
      final request = http.MultipartRequest('POST', Uri.parse('$baseUrl/predict/video-frame'));
      request.files.add(http.MultipartFile.fromBytes('file', videoBytes, filename: 'frame.mp4'));
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);
      if (response.statusCode == 200) {
        final result = jsonDecode(response.body);
        final newStatus = result['status'] ?? '';
        if (!mounted) return;
        setState(() => _status = newStatus);

        if (newStatus == 'DANGER') {
          _stomachSeconds += 3;
          if (_stomachSeconds >= 10 && !_alertSent) {
            _alertSent = true;
            _analysisTimer?.cancel();
            setState(() => _showAlert = true);
            // Send ONE notification only
            if (!_notificationSent) {
              _notificationSent = true;
              await NotificationService.showDangerAlert();
            }
          }
        } else if (newStatus == 'FACE_COVERED' && !_alertSent) {
          _alertSent = true;
          _analysisTimer?.cancel();
          setState(() => _showAlert = true);
          if (!_notificationSent) {
            _notificationSent = true;
            await NotificationService.showFaceCoveredAlert();
          }
        } else {
          _stomachSeconds = 0;
        }
      }
    } catch (e) {
      print('Error: $e');
    }
  }

  void _showCallOptions() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(28))),
      builder: (context) => Padding(
        padding: const EdgeInsets.fromLTRB(24, 12, 24, 32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(width: 36, height: 4, decoration: BoxDecoration(color: const Color(0xFFE0E0E0), borderRadius: BorderRadius.circular(2))),
            const SizedBox(height: 24),
            const Text('Call for Help', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: Color(0xFF1A1A1A))),
            const SizedBox(height: 8),
            const Text('Choose who to contact', style: TextStyle(fontSize: 14, color: Color(0xFF888888))),
            const SizedBox(height: 24),
            _callOption('Ambulance', '911', Icons.local_hospital_rounded, Colors.red, () { Navigator.pop(context); _makeCall('911'); }),
            const SizedBox(height: 12),
            _callOption('Emergency Contact', _emergencyPhone.isNotEmpty ? _emergencyPhone : 'Not set', Icons.person_rounded, const Color(0xFF6B7F5E), () { Navigator.pop(context); _makeCall(_emergencyPhone); }),
          ],
        ),
      ),
    );
  }

  Widget _callOption(String title, String sub, IconData icon, Color color, VoidCallback onTap) {
    return Material(
      color: color.withOpacity(0.06),
      borderRadius: BorderRadius.circular(18),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(18),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                width: 48, height: 48,
                decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(14)),
                child: Icon(icon, color: Colors.white, size: 24),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16, color: Color(0xFF1A1A1A))),
                    Text(sub, style: const TextStyle(color: Color(0xFF888888), fontSize: 13)),
                  ],
                ),
              ),
              Container(
                width: 32, height: 32,
                decoration: BoxDecoration(color: color.withOpacity(0.15), shape: BoxShape.circle),
                child: Icon(Icons.call_rounded, color: color, size: 16),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _makeCall(String number) async {
    final Uri url = Uri(scheme: 'tel', path: number);
    if (await canLaunchUrl(url)) await launchUrl(url);
  }

  void _stopAlarm() {
    setState(() {
      _showAlert = false;
      _alertSent = false;
      _notificationSent = false;
      _status = '';
      _stomachSeconds = 0;
    });
    _startAnalysis();
  }

  @override
  void dispose() {
    _analysisTimer?.cancel();
    _videoController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF7F3EE),
      body: SafeArea(
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Padding(
                padding: const EdgeInsets.fromLTRB(24, 20, 24, 8),
                child: Row(
                  children: [
                    Container(
                      width: 40, height: 40,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle, color: Colors.white,
                        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.08), blurRadius: 10)],
                      ),
                      child: ClipOval(child: Image.asset('assets/logo.png', fit: BoxFit.cover)),
                    ),
                    const SizedBox(width: 12),
                    const Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Mahd', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: Color(0xFF6B7F5E), letterSpacing: 0.5)),
                        Text('Baby Monitor', style: TextStyle(fontSize: 12, color: Color(0xFF999999), fontWeight: FontWeight.w500)),
                      ],
                    ),
                    const Spacer(),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: _showAlert ? Colors.red.withOpacity(0.1) : const Color(0xFF6B7F5E).withOpacity(0.1),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Row(
                        children: [
                          Container(width: 8, height: 8,
                            decoration: BoxDecoration(
                              color: _showAlert ? Colors.red : const Color(0xFF6B7F5E),
                              shape: BoxShape.circle,
                            ),
                          ),
                          const SizedBox(width: 6),
                          Text(
                            _showAlert ? 'DANGER' : _status == 'SAFE' ? 'SAFE' : 'MONITORING',
                            style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700,
                              color: _showAlert ? Colors.red : const Color(0xFF6B7F5E)),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 16),

              // Video - stable, no animation
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Container(
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(24),
                    border: _showAlert ? Border.all(color: Colors.red, width: 2.5) : null,
                    boxShadow: [
                      BoxShadow(
                        color: _showAlert ? Colors.red.withOpacity(0.2) : Colors.black.withOpacity(0.12),
                        blurRadius: 24, offset: const Offset(0, 8),
                      ),
                    ],
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(22),
                    child: SizedBox(
                      height: 260,
                      child: _videoController.value.isInitialized
                          ? Stack(
                              children: [
                                SizedBox.expand(
                                  child: FittedBox(
                                    fit: BoxFit.cover,
                                    child: SizedBox(
                                      width: _videoController.value.size.width,
                                      height: _videoController.value.size.height,
                                      child: VideoPlayer(_videoController),
                                    ),
                                  ),
                                ),
                                Positioned(
                                  top: 14, left: 14,
                                  child: Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                                    decoration: BoxDecoration(
                                      color: Colors.black.withOpacity(0.5),
                                      borderRadius: BorderRadius.circular(20),
                                    ),
                                    child: Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        Container(width: 6, height: 6, decoration: const BoxDecoration(color: Colors.red, shape: BoxShape.circle)),
                                        const SizedBox(width: 5),
                                        const Text('LIVE', style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w700, letterSpacing: 1)),
                                      ],
                                    ),
                                  ),
                                ),
                              ],
                            )
                          : Container(color: Colors.black, child: const Center(child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))),
                    ),
                  ),
                ),
              ),

              const SizedBox(height: 20),

              // Alert card
              if (_showAlert)
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: Colors.red.withOpacity(0.2)),
                      boxShadow: [BoxShadow(color: Colors.red.withOpacity(0.08), blurRadius: 20, spreadRadius: 2)],
                    ),
                    child: Column(
                      children: [
                        Row(
                          children: [
                            Container(
                              width: 48, height: 48,
                              decoration: BoxDecoration(color: Colors.red.withOpacity(0.1), borderRadius: BorderRadius.circular(14)),
                              child: const Icon(Icons.warning_rounded, color: Colors.red, size: 28),
                            ),
                            const SizedBox(width: 14),
                            const Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text('Danger Detected', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 17, color: Color(0xFF1A1A1A))),
                                  SizedBox(height: 2),
                                  Text('Baby on stomach!!', style: TextStyle(color: Colors.red, fontSize: 13, fontWeight: FontWeight.w500)),
                                ],
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),
                        Row(
                          children: [
                            Expanded(
                              child: TextButton.icon(
                                onPressed: _stopAlarm,
                                icon: const Icon(Icons.check_circle_outline, size: 20),
                                label: const Text('Checked', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
                                style: TextButton.styleFrom(
                                  foregroundColor: const Color(0xFF6B7F5E),
                                  backgroundColor: const Color(0xFF6B7F5E).withOpacity(0.1),
                                  padding: const EdgeInsets.symmetric(vertical: 14),
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                                ),
                              ),
                            ),
                            const SizedBox(width: 10),
                            Expanded(
                              child: TextButton.icon(
                                onPressed: _showCallOptions,
                                icon: const Icon(Icons.phone_rounded, size: 20),
                                label: const Text('Call for Help', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
                                style: TextButton.styleFrom(
                                  foregroundColor: Colors.white,
                                  backgroundColor: Colors.red,
                                  padding: const EdgeInsets.symmetric(vertical: 14),
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),

              // Safe status
              if (_status == 'SAFE' && !_showAlert)
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: const Color(0xFF6B7F5E).withOpacity(0.2)),
                    ),
                    child: const Row(
                      children: [
                        Icon(Icons.check_circle_rounded, color: Color(0xFF6B7F5E), size: 24),
                        SizedBox(width: 10),
                        Text('Baby is safe', style: TextStyle(color: Color(0xFF6B7F5E), fontSize: 15, fontWeight: FontWeight.w600)),
                      ],
                    ),
                  ),
                ),

              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }
}
