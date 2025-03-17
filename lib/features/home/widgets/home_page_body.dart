import 'package:commitz/core/providers/global_providers.dart';
import 'package:commitz/features/home/widgets/project_grid_view.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

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
        child: ProjectsGridView(
          userId: userId,
          deviceTypeConfig: deviceTypeConfig,
          projectNameController: projectNameController,
          youtubeUrlController: youtubeUrlController,
        ),
      ),
    );
  }
}
