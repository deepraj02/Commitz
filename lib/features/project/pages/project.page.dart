import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:commitz/core/helpers/responsive_layout.helper.dart';
import 'package:commitz/core/providers/global_providers.dart';
import 'package:commitz/features/project/widgets/responsive.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:skeletonizer/skeletonizer.dart';

class ProjectPage extends ConsumerWidget {
  static const String route = "/project";
  final String id;
  const ProjectPage({super.key, required this.id});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    var uiConfig =
        ProjectPageResponsiveConfig
            .responseiveUI[ResponsiveLayoutHelper.getDeviceType(context)];
    var deviceTypeConfig = ResponsiveLayoutHelper.getDeviceType(context);
    return StreamBuilder<DocumentSnapshot>(
      stream:
          FirebaseFirestore.instance
              .collection('users')
              .doc(ref.read(firebaseAuthInstanceProvider).currentUser!.uid)
              .snapshots(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return Skeletonizer(
            enabled: true,
            enableSwitchAnimation: true,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: GridView.builder(
                    padding: EdgeInsets.all(16.0),
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
                    itemCount: 6,
                    itemBuilder: (context, index) {
                      return Card(
                        elevation: 4.0,
                        child: Padding(
                          padding: const EdgeInsets.all(12.0),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Container(
                                height: 20,
                                width: double.infinity,
                                color: Colors.white,
                              ),
                              const Spacer(),
                              Container(
                                height: 16,
                                width: 100,
                                color: Colors.white,
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ],
            ),
          );
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
                      : GridView.builder(
                        padding: EdgeInsets.all(16.0),
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
                        itemCount: issues.length,
                        itemBuilder: (context, index) {
                          final issue = issues[index];
                          return InkWell(
                            onTap: () {
                              _showIssueDetails(context, issue);
                            },
                            child: Card(
                              elevation: 4.0,
                              child: Padding(
                                padding: const EdgeInsets.all(12.0),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Expanded(
                                      child: Text(
                                        issue['title'] ?? "Untitled Issue",
                                        style: TextStyle(
                                          fontWeight: FontWeight.w600,
                                          fontSize: 16.0,
                                        ),
                                        maxLines: 2,
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                    ),
                                    Row(
                                      mainAxisAlignment: MainAxisAlignment.end,
                                      children: [
                                        Icon(
                                          Icons.info_outline,
                                          size: 16.0,
                                          color: Colors.grey,
                                        ),
                                        SizedBox(width: 4.0),
                                        Text(
                                          'Tap for details',
                                          style: TextStyle(
                                            fontSize: 12.0,
                                            color: Colors.grey,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
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

  void _showIssueDetails(BuildContext context, Map<String, dynamic> issue) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16.0)),
      ),
      builder: (BuildContext context) {
        return DraggableScrollableSheet(
          initialChildSize: 0.6,
          minChildSize: 0.3,
          maxChildSize: 0.9,
          expand: false,
          builder: (context, scrollController) {
            return SingleChildScrollView(
              controller: scrollController,
              padding: EdgeInsets.all(20.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Center(
                    child: Container(
                      width: 40.0,
                      height: 5.0,
                      margin: EdgeInsets.only(bottom: 20.0),
                      decoration: BoxDecoration(
                        color: Colors.grey[300],
                        borderRadius: BorderRadius.circular(2.5),
                      ),
                    ),
                  ),
                  Text(
                    issue['title'] ?? "Untitled Issue",
                    style: TextStyle(
                      fontSize: 20.0,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  SizedBox(height: 16.0),
                  Text(
                    "Description",
                    style: TextStyle(
                      fontSize: 16.0,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  SizedBox(height: 8.0),
                  SelectableText(
                    issue['description'] ?? "No description",
                    style: TextStyle(fontSize: 14.0),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }
}
