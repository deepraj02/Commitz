import 'package:commitz/core/helpers/text.dart';
import 'package:commitz/features/home/widgets/home_page_body.dart';
import 'package:commitz/features/home/widgets/logout_button.dart';
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
                LogoutButton(ref: ref),
              ],
            ),
          ),
          HomePageBody(
            deviceTypeConfig: deviceTypeConfig,
            projectNameController: projectNameController,
            youtubeUrlController: youtubeUrlController,
          ),
        ],
      ),
    );
  }
}
