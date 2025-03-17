import 'package:flutter/material.dart';
import 'package:forui/forui.dart';

class SubmitButton extends StatelessWidget {
  const SubmitButton({
    super.key,
    required this.isProcessing,
    required this.onPress,
  });

  final bool isProcessing;
  final VoidCallback? onPress;

  @override
  Widget build(BuildContext context) {
    return FButton(
      label: isProcessing ? const LoadingIndicator() : const Text('Create'),
      onPress: isProcessing ? null : onPress,
    );
  }
}

// Loading indicator component
class LoadingIndicator extends StatelessWidget {
  const LoadingIndicator({super.key});

  @override
  Widget build(BuildContext context) {
    return const SizedBox(
      height: 20,
      width: 20,
      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
    );
  }
}
