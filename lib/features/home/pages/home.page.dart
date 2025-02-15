import 'package:commitz/features/auth/providers/github.service.provider.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:forui/forui.dart';

class HomePage extends ConsumerWidget {
  static const String route = "/home";
  const HomePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          MaterialButton(
            onPressed: () {
              ref.read(githubAuthProvider.notifier).signOut();
            },
            child: Text('Logout'),
          ),
          IntrinsicWidth(
            child: FButton(
              label: const Text('Show Dialog'),
              onPress:
                  () => showAdaptiveDialog(
                    context: context,
                    builder:
                        (context) => FDialog(
                          direction: Axis.vertical,
                          title: const Text('Create a new Project'),
                          body: const Text(
                            'This action cannot be undone. This will permanently delete your account and remove your data from our servers.',
                          ),
                          actions: [
                            FButton(
                              label: const Text('Continue'),
                              onPress: () => Navigator.of(context).pop(),
                            ),
                            FButton(
                              style: FButtonStyle.outline,
                              label: const Text('Cancel'),
                              onPress: () => Navigator.of(context).pop(),
                            ),
                          ],
                        ),
                  ),
            ),
          ),
        ],
      ),
    );
  }
}

class PopOverWidget extends StatelessWidget {
  const PopOverWidget({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        IntrinsicWidth(
          child: FButton(
            label: const Text('Show Dialog'),
            onPress:
                () => showAdaptiveDialog(
                  context: context,
                  builder:
                      (context) => FDialog(
                        direction: Axis.vertical,
                        title: const Text('Are you absolutely sure?'),
                        body: const Text(
                          'This action cannot be undone. This will permanently delete your account and remove your data from our servers.',
                        ),
                        actions: [
                          FButton(
                            label: const Text('Continue'),
                            onPress: () => Navigator.of(context).pop(),
                          ),
                          FButton(
                            style: FButtonStyle.outline,
                            label: const Text('Cancel'),
                            onPress: () => Navigator.of(context).pop(),
                          ),
                        ],
                      ),
                ),
          ),
        ),
      ],
    );
  }
}
