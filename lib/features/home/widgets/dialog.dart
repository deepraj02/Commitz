import 'package:commitz/core/helpers/input_validators.dart';
import 'package:commitz/core/providers/global_providers.dart';
import 'package:commitz/features/home/providers/transcript_service.provider.dart';
import 'package:commitz/features/home/state/home.state.dart';
import 'package:commitz/features/home/widgets/formfield.dart';
import 'package:commitz/features/home/widgets/submit_button.dart';
import 'package:commitz/features/project/pages/project.page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:forui/forui.dart';
import 'package:go_router/go_router.dart';

import '../services/firestore.service.dart';

class ProjectDialog extends ConsumerStatefulWidget {
  const ProjectDialog({
    super.key,
    required this.projectNameController,
    required this.youtubeUrlController,
  });

  final TextEditingController projectNameController;
  final TextEditingController youtubeUrlController;

  @override
  ConsumerState<ProjectDialog> createState() => _ProjectDialogState();
}

class _ProjectDialogState extends ConsumerState<ProjectDialog> {
  bool _isSubmitting = false;
  final _formKey = GlobalKey<FormState>();

  Future<void> _handleSubmit() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() => _isSubmitting = true);

    try {
      final projectName = widget.projectNameController.text.trim();
      final youtubeUrl = widget.youtubeUrlController.text.trim();

      final projectResult = await ref
          .read(firestoreProvider)
          .createMetadata(projectName);

      projectResult.fold(
        (error) => _handleError('Error creating project: $error'),
        (projectId) => _processTranscript(projectId, youtubeUrl),
      );
    } catch (e) {
      _handleError('Error: $e');
    }
  }

  Future<void> _processTranscript(String projectId, String youtubeUrl) async {
    final apiResult = await ref
        .read(videoTranscriptProvider.notifier)
        .getTranscript(youtubeUrl);

    apiResult.fold(
      (error) => _handleError('Error getting transcript: $error'),
      (issues) => _saveIssues(projectId, issues),
    );
  }

  Future<void> _saveIssues(
    String projectId,
    Map<String, dynamic> issues,
  ) async {
    final userId = ref.read(firebaseAuthInstanceProvider).currentUser!.uid;

    final issuesList =
        (issues['issues'] as List)
            .map(
              (issue) => {
                'title': issue['title'],
                'description': issue['description'],
              },
            )
            .toList();

    await ref
        .read(firestoreProvider)
        .addIssuesToProject(userId, projectId, issuesList);

    setState(() => _isSubmitting = false);

    if (mounted) {
      Navigator.of(context).pop();
      context.goNamed(ProjectPage.route, queryParameters: {'id': projectId});
    }
  }

  void _handleError(String message) {
    setState(() => _isSubmitting = false);

    if (mounted) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(message)));
    }
  }

  @override
  Widget build(BuildContext context) {
    final transcriptState = ref.watch(videoTranscriptProvider);
    final isProcessing =
        _isSubmitting || transcriptState is HomePageStateLoading;

    return FDialog(
      direction: Axis.vertical,
      title: const Text('Create a new Project'),
      body: Form(
        key: _formKey,
        child: Flex(
          spacing: 20,
          direction: Axis.vertical,
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            CommitzFormField(
              controller: widget.projectNameController,
              label: 'Project Name',
              hint: 'Enter the name of the project',
              enabled: !isProcessing,
              validator: validateProjectName,
            ),
            CommitzFormField(
              controller: widget.youtubeUrlController,
              label: 'Youtube URL',
              hint: 'Enter the link of the youtube video',
              enabled: !isProcessing,
              validator: validateYoutubeUrl,
            ),
          ],
        ),
      ),
      actions: [
        FButton(
          style: FButtonStyle.outline,
          label: const Text('Cancel'),
          onPress: isProcessing ? null : () => Navigator.of(context).pop(),
        ),
        SubmitButton(isProcessing: isProcessing, onPress: _handleSubmit),
      ],
    );
  }
}
