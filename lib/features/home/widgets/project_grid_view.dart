import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:commitz/core/helpers/responsive_layout.helper.dart';
import 'package:commitz/core/providers/global_providers.dart';
import 'package:commitz/features/home/widgets/create_project_tile.dart';
import 'package:commitz/features/home/widgets/empty_tile.dart';
import 'package:commitz/features/home/widgets/project_tile.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class ProjectsGridView extends ConsumerWidget {
  const ProjectsGridView({
    super.key,
    required this.userId,
    required this.deviceTypeConfig,
    required this.projectNameController,
    required this.youtubeUrlController,
  });

  final String userId;
  final DeviceType deviceTypeConfig;
  final TextEditingController projectNameController;
  final TextEditingController youtubeUrlController;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    List<Map<String, dynamic>> extractProjects(
      AsyncSnapshot<DocumentSnapshot> snapshot,
    ) {
      if (!snapshot.hasData || !snapshot.data!.exists) {
        return [];
      }

      final data = snapshot.data!.data() as Map<String, dynamic>?;
      if (data == null ||
          !data.containsKey('Projectsv3') ||
          data['Projectsv3'] == null) {
        return [];
      }

      final projectsList = List<Map<String, dynamic>>.from(
        data['Projectsv3'].map((p) => Map<String, dynamic>.from(p)),
      );

      projectsList.sort((a, b) {
        final aDate = a['created_at'] ?? 0;
        final bDate = b['created_at'] ?? 0;
        return bDate.compareTo(aDate);
      });

      return projectsList;
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

        final projects = extractProjects(snapshot);
        final itemCount = projects.length + 1;

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
              return CreateProjectTile(
                projectNameController: projectNameController,
                youtubeUrlController: youtubeUrlController,
              );
            }

            final projectIndex = index - 1;
            if (projectIndex < projects.length) {
              return ProjectTile(project: projects[projectIndex]);
            }
            return EmptyTile();
          },
          itemCount: itemCount,
        );
      },
    );
  }
}
