import 'package:commitz/features/project/pages/project.page.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

class ProjectTile extends StatelessWidget {
  const ProjectTile({super.key, required this.project});

  final Map<String, dynamic> project;

  @override
  Widget build(BuildContext context) {
    final projectId = project['project_id'] as String;
    final name = project['name'] as String? ?? 'Unnamed Project';
    final timestamp = project['created_at'] as int? ?? 0;
    final issueCount = (project['issues'] as List?)?.length ?? 0;

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
                style: TextStyle(fontSize: 12, color: Colors.grey[600]),
              ),
              const SizedBox(height: 12),
              Text('$issueCount issues', style: const TextStyle(fontSize: 14)),
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
}
