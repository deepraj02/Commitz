import 'package:commitz/core/helpers/text.dart';
import 'package:commitz/features/auth/providers/github.service.provider.dart';
import 'package:commitz/features/home/widgets/dialog.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:skeletonizer/skeletonizer.dart';

import '../../../core/helpers/responsive_layout.helper.dart';
import 'responsive.dart';

class HomePage extends ConsumerStatefulWidget {
  static const String route = "/home";
  const HomePage({super.key});

  @override
  ConsumerState<ConsumerStatefulWidget> createState() => _HomePageState();
}

class _HomePageState extends ConsumerState<HomePage> {
  bool enableSkeletonizer = true;

  @override
  void initState() {
    super.initState();
    Future.delayed(const Duration(milliseconds: 800), () {
      setState(() {
        enableSkeletonizer = false;
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    final projectNameController = TextEditingController();
    final youtubeUrlController = TextEditingController();

    var uiConfig =
        HomePageResponsiveConfig
            .responseiveUI[ResponsiveLayoutHelper.getDeviceType(context)];
    var deviceTypeConfig = ResponsiveLayoutHelper.getDeviceType(context);

    return Skeletonizer(
      enabled: enableSkeletonizer,
      enableSwitchAnimation: true,
      child: Column(
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
          ),
        ],
      ),
    );
  }
}
