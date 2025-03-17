import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:commitz/core/providers/global_providers.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class ProjectPage extends ConsumerWidget {
  static const String route = "/project";
  final String id;
  const ProjectPage({super.key, required this.id});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return StreamBuilder<DocumentSnapshot>(
      stream:
          FirebaseFirestore.instance
              .collection('users')
              .doc(ref.read(firebaseAuthInstanceProvider).currentUser!.uid)
              .snapshots(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return Center(child: CircularProgressIndicator());
        }

        if (!snapshot.hasData || snapshot.data == null) {
          return Center(child: Text("No project data found"));
        }

        final userData = snapshot.data!.data() as Map<String, dynamic>;
        final projects = List.from(userData['Projectsv3'] ?? []);

        final project = projects.firstWhere(
          (p) => p['project_id'] == id,
          orElse: () => null,
        );

        if (project == null) {
          return Center(child: Text("Project not found"));
        }

        final issues = List.from(project['issues'] ?? []);

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: Text(
                project['name'] ?? "Unnamed Project",
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              ),
            ),
            Expanded(
              child:
                  issues.isEmpty
                      ? Center(child: Text("No issues found"))
                      : ListView.builder(
                        itemCount: issues.length,
                        itemBuilder: (context, index) {
                          final issue = issues[index];
                          return Card(
                            margin: EdgeInsets.symmetric(
                              horizontal: 16.0,
                              vertical: 8.0,
                            ),
                            child: ExpansionTile(
                              title: Text(
                                issue['title'] ?? "Untitled Issue",
                                style: TextStyle(fontWeight: FontWeight.w600),
                              ),
                              children: [
                                Padding(
                                  padding: const EdgeInsets.all(16.0),
                                  child: SelectableText(
                                    issue['description'] ?? "No description",
                                  ),
                                ),
                              ],
                            ),
                          );
                        },
                      ),
            ),
          ],
        );
      },
    );
  }
}
