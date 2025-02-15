import 'package:commitz/core/router/app.router.dart';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class Commitz extends ConsumerWidget {
  const Commitz({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final routerConfig = ref.read(routerProvider);
    return MaterialApp.router(
      theme: ThemeData.dark(),
      themeMode: ThemeMode.dark,
      debugShowCheckedModeBanner: false,
      routerDelegate: routerConfig.routerDelegate,
      routeInformationParser: routerConfig.routeInformationParser,
      routeInformationProvider: routerConfig.routeInformationProvider,
    ).animate().fadeIn();
  }
}
