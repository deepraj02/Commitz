import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:commitz/core/providers/global_providers.dart';
import 'package:commitz/features/home/widgets/dialog.dart';
import 'package:commitz/features/project/pages/project.page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../core/helpers/responsive_layout.helper.dart';

class HomePageBody extends ConsumerWidget {
  const HomePageBody({
    super.key,
    required this.deviceTypeConfig,
    required this.projectNameController,
    required this.youtubeUrlController,
  });

  final DeviceType deviceTypeConfig;
  final TextEditingController projectNameController;
  final TextEditingController youtubeUrlController;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final userId = ref.read(firebaseAuthInstanceProvider).currentUser?.uid;

    if (userId == null) {
      return const Center(child: Text('Please sign in to view your projects'));
    }

    return Expanded(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: StreamBuilder<DocumentSnapshot>(
          stream:
              ref
                  .read(firestoreInstanceProvider)
                  .collection('users')
                  .doc(userId)
                  .snapshots(),
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }

            List<Map<String, dynamic>> projects = [];
            int itemCount = 1; // Start with 1 for the create project tile

            if (snapshot.hasData && snapshot.data!.exists) {
              final data = snapshot.data!.data() as Map<String, dynamic>?;
              if (data != null &&
                  data.containsKey('Projectsv3') &&
                  data['Projectsv3'] != null) {
                projects = List<Map<String, dynamic>>.from(
                  data['Projectsv3'].map((p) => Map<String, dynamic>.from(p)),
                );

                // Sort projects by creation date (newest first)
                projects.sort((a, b) {
                  final aDate = a['created_at'] ?? 0;
                  final bDate = b['created_at'] ?? 0;
                  return bDate.compareTo(aDate);
                });

                itemCount = projects.length + 1; // +1 for create project tile
              }
            }

            return GridView.builder(
              gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount:
                    deviceTypeConfig == DeviceType.desktop
                        ? 3
                        : deviceTypeConfig == DeviceType.tab
                        ? 2
                        : 1,
                childAspectRatio: 3 / 2,
                crossAxisSpacing: 16.0,
                mainAxisSpacing: 16.0,
              ),
              itemBuilder: (context, index) {
                if (index == 0) {
                  // Keep the create project tile as it is
                  return InkWell(
                    onTap: () {
                      showDialog(
                        context: context,
                        builder: (context) {
                          return ProjectDialog(
                            projectNameController: projectNameController,
                            youtubeUrlController: youtubeUrlController,
                          );
                        },
                      );
                    },
                    child: Container(
                      decoration: BoxDecoration(
                        color: Colors.grey.withAlpha(15),
                        borderRadius: BorderRadius.circular(8.0),
                      ),
                      child: Center(child: Text('Create Project')),
                    ),
                  );
                }

                // Project tiles - use actual project data
                final projectIndex =
                    index - 1; // Adjust for create project tile
                if (projectIndex < projects.length) {
                  final project = projects[projectIndex];
                  final projectId = project['project_id'] as String;
                  final name = project['name'] as String? ?? 'Unnamed Project';
                  final timestamp = project['created_at'] as int? ?? 0;
                  final issueCount = (project['issues'] as List?)?.length ?? 0;

                  // Format date
                  final date = DateTime.fromMillisecondsSinceEpoch(timestamp);
                  final formattedDate = DateFormat('MMM d, yyyy').format(date);

                  return InkWell(
                    onTap:
                        () => context.pushNamed(
                          ProjectPage.route,
                          queryParameters: {'id': projectId},
                        ),
                    child: Container(
                      decoration: BoxDecoration(
                        color: Colors.blueGrey.withAlpha(15),
                        borderRadius: BorderRadius.circular(8.0),
                      ),
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              name,
                              style: const TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                            const SizedBox(height: 8),
                            Text(
                              'Created on $formattedDate',
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.grey[600],
                              ),
                            ),
                            const SizedBox(height: 12),
                            Text(
                              '$issueCount issues',
                              style: const TextStyle(fontSize: 14),
                            ),
                            const Spacer(),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.end,
                              children: [
                                Icon(
                                  Icons.arrow_forward,
                                  color: Theme.of(context).primaryColor,
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),
                  );
                }

                // Fallback for any extra slots
                return Container(
                  decoration: BoxDecoration(
                    color: Colors.blueGrey.withAlpha(4),
                    borderRadius: BorderRadius.circular(8.0),
                  ),
                );
              },
              itemCount: itemCount,
            );
          },
        ),
      ),
    );
  }
}
