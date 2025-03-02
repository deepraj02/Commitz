import '../../../core/helpers/responsive_layout.helper.dart' show DeviceType;

class LandingPageResponsiveConfig {
  final double titleSize;
  final double subTitleSize;
  final double buttonSize;

  LandingPageResponsiveConfig({
    required this.titleSize,
    required this.subTitleSize,
    required this.buttonSize,
  });

  static Map<DeviceType, LandingPageResponsiveConfig> responseiveUI = {
    DeviceType.mobile: LandingPageResponsiveConfig(
      titleSize: 50,
      subTitleSize: 15,
      buttonSize: 20,
    ),
    DeviceType.tab: LandingPageResponsiveConfig(
      titleSize: 80,
      subTitleSize: 25,
      buttonSize: 30,
    ),
    DeviceType.desktop: LandingPageResponsiveConfig(
      titleSize: 100,
      subTitleSize: 35,
      buttonSize: 50,
    ),
  };
}
