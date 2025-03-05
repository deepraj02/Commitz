import 'package:commitz/core/providers/global_providers.dart';
import 'package:commitz/features/home/providers/transcript_service.provider.dart';
import 'package:commitz/features/home/state/home.state.dart';
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
  bool _isLoading = false;

  @override
  Widget build(BuildContext context) {
    final newState = ref.watch(videoTranscriptProvider);

    // This will ensure we reflect the provider state correctly
    bool isLoading = _isLoading || newState is HomePageStateLoading;

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
            controller: widget.projectNameController,
            label: const Text('Project Name'),
            hint: 'Enter the name of the project',
            enabled: !isLoading,
          ),
          FTextField(
            controller: widget.youtubeUrlController,
            label: const Text('Youtube URL'),
            hint: 'Enter the link of the youtube video',
            enabled: !isLoading,
          ),
        ],
      ),
      actions: [
        FButton(
          style: FButtonStyle.outline,
          label: const Text('Cancel'),
          onPress: isLoading ? null : () => Navigator.of(context).pop(),
        ),
        FButton(
          label:
              isLoading
                  ? const SizedBox(
                    height: 20,
                    width: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: Colors.white,
                    ),
                  )
                  : const Text('Create'),
          onPress:
              isLoading
                  ? null
                  : () async {
                    try {
                      setState(() {
                        _isLoading = true;
                      });

                      // 1. Create the project metadata first
                      final projectResult = await ref
                          .read(firestoreProvider)
                          .createMetadata(
                            widget.projectNameController.text.trim(),
                          );

                      projectResult.fold(
                        (error) {
                          setState(() {
                            _isLoading = false;
                          });

                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text(
                                "Error creating project: ${error.toString()}",
                              ),
                            ),
                          );
                        },
                        (projectId) async {
                          // 2. Get the issues from the API
                          final apiResult = await ref
                              .read(videoTranscriptProvider.notifier)
                              .getTranscript(
                                widget.youtubeUrlController.text.trim(),
                              );

                          apiResult.fold(
                            (error) {
                              setState(() {
                                _isLoading = false;
                              });

                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text(
                                    "Error getting transcript: $error",
                                  ),
                                ),
                              );
                            },
                            (issues) async {
                              // 3. Add each issue to the project
                              final userId =
                                  ref
                                      .read(firebaseAuthInstanceProvider)
                                      .currentUser!
                                      .uid;

                              // Create a list of all issues to add
                              List<Map<String, dynamic>> issuesList = [];
                              for (var issue in issues['issues']) {
                                issuesList.add({
                                  'title': issue['title'],
                                  'description': issue['description'],
                                });
                              }

                              // Add all issues in one batch operation
                              await ref
                                  .read(firestoreProvider)
                                  .addIssuesToProject(
                                    userId,
                                    projectId,
                                    issuesList,
                                  );

                              // Reset loading state
                              setState(() {
                                _isLoading = false;
                              });

                              // 4. Close dialog and navigate to project
                              Navigator.of(context).pop();
                              context.goNamed(
                                ProjectPage.route,
                                queryParameters: {'id': projectId},
                              );
                            },
                          );
                        },
                      );
                    } catch (e) {
                      setState(() {
                        _isLoading = false;
                      });

                      print(e);
                      ScaffoldMessenger.of(
                        context,
                      ).showSnackBar(SnackBar(content: Text("Error: $e")));
                    }
                  },
        ),
      ],
    );
  }
}
