import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../auth/providers/github_auth_service.provider.dart';

class LogoutButton extends StatelessWidget {
  const LogoutButton({super.key, required this.ref});

  final WidgetRef ref;

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      cursor: SystemMouseCursors.click,
      child: MaterialButton(
        onPressed: () {
          ref.read(githubAuthProvider.notifier).signOut();
        },
        child: Text('Logout'),
      ),
    );
  }
}
