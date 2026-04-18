import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = 'http://127.0.0.1:8000/api';

  static Future<Map<String, dynamic>> analyzeFrame(Uint8List frameBytes) async {
    try {
      final base64Image = base64Encode(frameBytes);
      final response = await http.post(
        Uri.parse('$baseUrl/predict'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'image': base64Image}),
      );
      if (response.statusCode == 200) {
        final result = jsonDecode(response.body);
        print('API Result: $result');
        return result;
      } else {
        return {'status': 'ERROR'};
      }
    } catch (e) {
      print('API Error: $e');
      return {'status': 'ERROR'};
    }
  }
}
