import 'dart:developer';

import 'package:commitz/core/helpers/text.dart';
import 'package:commitz/features/auth/providers/github.service.provider.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:forui/forui.dart';

import '../../../core/helpers/responsive_layout.helper.dart';
import 'responsive.dart';

class HomePage extends ConsumerWidget {
  static const String route = "/home";
  const HomePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final projectNameController = TextEditingController();
    final youtubeUrlController = TextEditingController();

    var uiConfig =
        HomePageResponsiveConfig
            .responseiveUI[ResponsiveLayoutHelper.getDeviceType(context)];

    return Column(
      mainAxisAlignment: MainAxisAlignment.start,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Padding(
          padding: const EdgeInsets.only(top: 15.0, left: 15.0, right: 15.0),
          child: Flex(
            direction: Axis.horizontal,
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              CommitzText.gradient(
                text: "My Projects",
                colors: [Colors.redAccent, Colors.amberAccent],
                fontSize: uiConfig!.subTitleSize,
              ),
              MouseRegion(
                cursor: SystemMouseCursors.click,
                child: MaterialButton(
                  onPressed: () {
                    ref.read(githubAuthProvider.notifier).signOut();
                  },
                  child: Text('Logout'),
                ),
              ),
            ],
          ),
        ),
        Expanded(
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: GridView.builder(
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 3,
                childAspectRatio: 3 / 2,
                crossAxisSpacing: 16.0,
                mainAxisSpacing: 16.0,
              ),
              itemBuilder: (context, index) {
                if (index == 0) {
                  return InkWell(
                    onTap: () {
                      showAdaptiveDialog(
                        context: context,
                        builder: (context) {
                          return FDialog(
                            direction: Axis.vertical,
                            title: const Text('Create a new Project'),
                            body: Flex(
                              direction: Axis.vertical,
                              mainAxisAlignment: MainAxisAlignment.center,
                              crossAxisAlignment: CrossAxisAlignment.center,
                              children: [
                                FTextField(
                                  controller: projectNameController,
                                  label: const Text('Project Name'),
                                  hint: 'Enter the name of the project',
                                ),
                                FTextField(
                                  controller: youtubeUrlController,
                                  label: const Text('Youtube URL'),
                                  hint: 'Enter the link of the youtube video',
                                ),
                              ],
                            ),
                            actions: [
                              FButton(
                                label: const Text('Continue'),
                                onPress: () {
                                  log(
                                    ' ${projectNameController.text}, ${youtubeUrlController.text}',
                                  );
                                  Navigator.of(context).pop();
                                },
                              ),
                              FButton(
                                style: FButtonStyle.outline,
                                label: const Text('Cancel'),
                                onPress: () => Navigator.of(context).pop(),
                              ),
                            ],
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
        ),
      ],
    );
  }
}

class PopOverWidget extends StatelessWidget {
  const PopOverWidget({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        IntrinsicWidth(
          child: FButton(
            label: const Text('Show Dialog'),
            onPress:
                () => showAdaptiveDialog(
                  context: context,
                  builder:
                      (context) => FDialog(
                        direction: Axis.vertical,
                        title: const Text('Are you absolutely sure?'),
                        body: const Text(
                          'This action cannot be undone. This will permanently delete your account and remove your data from our servers.',
                        ),
                        actions: [
                          FButton(
                            label: const Text('Continue'),
                            onPress: () => Navigator.of(context).pop(),
                          ),
                          FButton(
                            style: FButtonStyle.outline,
                            label: const Text('Cancel'),
                            onPress: () => Navigator.of(context).pop(),
                          ),
                        ],
                      ),
                ),
          ),
        ),
      ],
    );
  }
}
