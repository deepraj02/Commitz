import 'package:commitz/core/helpers/responsive_layout.helper.dart';
import 'package:commitz/features/auth/providers/github.service.provider.dart';
import 'package:commitz/features/landing/pages/responsive.config.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:modular_ui/modular_ui.dart';

import '../../../core/helpers/text.dart';

class LandingPage extends ConsumerWidget {
  static const String route = "/";
  const LandingPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    var uiConfig =
        LandingPageResponsiveConfig
            .responseiveUI[ResponsiveLayoutHelper.getDeviceType(context)];
    return Center(
      child: Column(
        spacing: 10,
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: <Widget>[
          CommitzText.gradient(text: "Commitz", fontSize: uiConfig!.titleSize),
          CommitzText(
            text:
                "convert long boring youtube videos into \n interactive github issues",
            fontSize: uiConfig.subTitleSize,
            textAlign: TextAlign.center,
          ),
          MouseRegion(
            cursor: SystemMouseCursors.click,
            child: MUISecondaryButton(
              text: "Get Started",
              onPressed: () {
                ref.read(githubAuthProvider.notifier).signInWithGithub();
              },
            ),
          ),
        ],
      ),
    );
  }
}
