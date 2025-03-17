import 'package:commitz/features/home/widgets/dialog.dart';
import 'package:flutter/material.dart';

class CreateProjectTile extends StatelessWidget {
  const CreateProjectTile({
    super.key,
    required this.projectNameController,
    required this.youtubeUrlController,
  });

  final TextEditingController projectNameController;
  final TextEditingController youtubeUrlController;

  @override
  Widget build(BuildContext context) {
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
        child: const Center(child: Text('Create Project')),
      ),
    );
  }
}
