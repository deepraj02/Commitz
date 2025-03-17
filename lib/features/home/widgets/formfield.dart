import 'package:flutter/material.dart';
import 'package:forui/forui.dart';

class CommitzFormField extends StatelessWidget {
  const CommitzFormField({
    super.key,
    required this.controller,
    required this.label,
    required this.hint,
    required this.validator,
    this.enabled = true,
  });

  final TextEditingController controller;
  final String label;
  final String hint;
  final String? Function(String?) validator;
  final bool enabled;

  @override
  Widget build(BuildContext context) {
    return FTextField(
      controller: controller,
      label: Text(label),
      hint: hint,
      enabled: enabled,
      validator: validator,
    );
  }
}
