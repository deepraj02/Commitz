import '../../../core/helpers/responsive_layout.helper.dart' show DeviceType;

class HomePageResponsiveConfig {
  final double titleSize;
  final double subTitleSize;
  final double buttonSize;

  HomePageResponsiveConfig({
    required this.titleSize,
    required this.subTitleSize,
    required this.buttonSize,
  });

  static Map<DeviceType, HomePageResponsiveConfig> responseiveUI = {
    DeviceType.mobile: HomePageResponsiveConfig(
      titleSize: 50,
      subTitleSize: 15,
      buttonSize: 20,
    ),
    DeviceType.tab: HomePageResponsiveConfig(
      titleSize: 80,
      subTitleSize: 25,
      buttonSize: 30,
    ),
    DeviceType.desktop: HomePageResponsiveConfig(
      titleSize: 100,
      subTitleSize: 35,
      buttonSize: 50,
    ),
  };
}
