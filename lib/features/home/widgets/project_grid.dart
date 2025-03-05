import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:commitz/core/providers/global_providers.dart';
import 'package:commitz/features/project/pages/project.page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
// ignore: depend_on_referenced_packages
import 'package:intl/intl.dart';

class ProjectsGrid extends ConsumerWidget {
  const ProjectsGrid({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final userId = ref.read(firebaseAuthInstanceProvider).currentUser?.uid;

    if (userId == null) {
      return const Center(child: Text('Please sign in to view your projects'));
    }

    return StreamBuilder<DocumentSnapshot>(
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

        if (snapshot.hasError) {
          return Center(child: Text('Error: ${snapshot.error}'));
        }

        if (!snapshot.hasData || !snapshot.data!.exists) {
          return const Center(
            child: Text('No projects found. Create your first project!'),
          );
        }

        final data = snapshot.data!.data() as Map<String, dynamic>?;
        if (data == null ||
            !data.containsKey('Projectsv3') ||
            data['Projectsv3'] == null) {
          return const Center(
            child: Text('No projects found. Create your first project!'),
          );
        }

        final projects = List<Map<String, dynamic>>.from(
          data['Projectsv3'].map((p) => Map<String, dynamic>.from(p)),
        );
        projects.sort((a, b) {
          final aDate = a['created_at'] ?? 0;
          final bDate = b['created_at'] ?? 0;
          return bDate.compareTo(aDate);
        });

        return GridView.builder(
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 2,
            crossAxisSpacing: 16,
            mainAxisSpacing: 16,
            childAspectRatio: 1.3,
          ),
          padding: const EdgeInsets.all(16),
          itemCount: projects.length,
          itemBuilder: (context, index) {
            final project = projects[index];
            final projectId = project['project_id'] as String;
            final name = project['name'] as String? ?? 'Unnamed Project';
            final timestamp = project['created_at'] as int? ?? 0;
            final issueCount = (project['issues'] as List?)?.length ?? 0;

            final date = DateTime.fromMillisecondsSinceEpoch(timestamp);
            final formattedDate = DateFormat('MMM d, yyyy').format(date);

            return GestureDetector(
              onTap:
                  () => context.pushNamed(
                    ProjectPage.route,
                    queryParameters: {'id': projectId},
                  ),
              child: Card(
                elevation: 4,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(16),
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
                        style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                      ),
                      const SizedBox(height: 12),
                      Text(
                        '$issueCount issues',
                        style: const TextStyle(fontSize: 14),
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        );
      },
    );
  }
}
