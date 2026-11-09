import 'dart:io' show Platform;
import 'package:flet/flet.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class KeystoreControl extends StatefulWidget {
  final Control? parent;
  final Control control;
  final Widget? nextChild;
  final FletControlBackend backend;

  const KeystoreControl({
    super.key,
    required this.parent,
    required this.control,
    required this.nextChild,
    required this.backend,
  });

  @override
  State<KeystoreControl> createState() => _KeystoreControlState();
}

class _KeystoreControlState extends State<KeystoreControl> {
  final FlutterSecureStorage storage = const FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
  );

  @override
  void initState() {
    super.initState();
    widget.backend.subscribeMethods(widget.control.id, (method, args) async {
      if (!Platform.isAndroid) return null;
      // The Flet bridge must not log arguments or returned secrets.
      final key = args['key'];
      if (key is! String || key != 'botking.dhan.server_access.v1') {
        return null;
      }
      try {
        switch (method) {
          case 'get':
            return await storage.read(key: key);
          case 'set':
            final value = args['value'];
            if (value is! String || value.isEmpty) return null;
            await storage.write(key: key, value: value);
            return '1';
          case 'delete':
            await storage.delete(key: key);
            return '1';
        }
      } catch (_) {
        // Fail closed; never expose native exception text or secrets.
        return null;
      }
      return null;
    });
  }

  @override
  Widget build(BuildContext context) => const SizedBox.shrink();
}
