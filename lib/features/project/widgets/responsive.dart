import '../../../core/helpers/responsive_layout.helper.dart' show DeviceType;

class ProjectPageResponsiveConfig {
  final double titleSize;
  final double subTitleSize;
  final double buttonSize;

  ProjectPageResponsiveConfig({
    required this.titleSize,
    required this.subTitleSize,
    required this.buttonSize,
  });

  static Map<DeviceType, ProjectPageResponsiveConfig> responseiveUI = {
    DeviceType.mobile: ProjectPageResponsiveConfig(
      titleSize: 50,
      subTitleSize: 15,
      buttonSize: 20,
    ),
    DeviceType.tab: ProjectPageResponsiveConfig(
      titleSize: 80,
      subTitleSize: 25,
      buttonSize: 30,
    ),
    DeviceType.desktop: ProjectPageResponsiveConfig(
      titleSize: 100,
      subTitleSize: 35,
      buttonSize: 50,
    ),
  };
}
