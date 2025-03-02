import 'package:commitz/features/home/widgets/dialog.dart';
import 'package:flutter/material.dart';

import '../../../core/helpers/responsive_layout.helper.dart';

class HomePageBody extends StatelessWidget {
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
  Widget build(BuildContext context) {
    return Expanded(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: GridView.builder(
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
            return Container(
              decoration: BoxDecoration(
                color: Colors.blueGrey.withAlpha(4),
                borderRadius: BorderRadius.circular(8.0),
              ),
            );
          },
          itemCount: 10,
        ),
      ),
    );
  }
}
