import 'dart:developer';

import 'package:flutter/material.dart';
import 'package:forui/forui.dart';

class ProjectDialog extends StatelessWidget {
  const ProjectDialog({
    super.key,
    required this.projectNameController,
    required this.youtubeUrlController,
  });

  final TextEditingController projectNameController;
  final TextEditingController youtubeUrlController;

  @override
  Widget build(BuildContext context) {
    return FDialog(
      direction: Axis.vertical,
      title: const Text('Create a new Project'),
      body: Flex(
        spacing: 20,
        direction: Axis.vertical,
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          FTextField(
            controller: projectNameController,
            label: const Text('Project Name'),
            hint: 'Enter the name of the project',
          ),
          FTextField(
            controller: youtubeUrlController,
            label: const Text('Youtube URL'),
            hint: 'Enter the link of the youtube video',
          ),
        ],
      ),
      actions: [
        FButton(
          style: FButtonStyle.outline,
          label: const Text('Cancel'),
          onPress: () => Navigator.of(context).pop(),
        ),
        FButton(
          label: const Text('Continue'),
          onPress: () {
            log(' ${projectNameController.text}, ${youtubeUrlController.text}');
            Navigator.of(context).pop();
          },
        ),
      ],
    );
  }
}
