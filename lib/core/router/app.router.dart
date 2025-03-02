import 'package:commitz/features/home/pages/home.page.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../features/auth/pages/landing.page.dart';
import '../providers/global_providers.dart';

part 'app.router.g.dart';

@riverpod
GoRouter router(RouterRef ref) {
  final navigatorKey = GlobalKey<NavigatorState>();
  final authStatus = ref.watch(firebaseAuthProvider);
  final authState = ref.watch(authStateProvider.stream);
  return GoRouter(
    navigatorKey: navigatorKey,
    debugLogDiagnostics: true,
    initialLocation: LandingPage.route,
    routes: [
      ShellRoute(
        builder: (BuildContext context, GoRouterState state, Widget child) {
          return Scaffold(
            backgroundColor: const Color(0xff0A0A0A),
            body: child,
          );
        },
        routes: [
          GoRoute(
            path: LandingPage.route,
            builder: (context, state) => LandingPage(),
          ),
          GoRoute(
            path: HomePage.route,
            builder: (context, state) => HomePage(),
          ),
          // GoRoute(
          //   path: '/project/:id',
          //   builder:
          //       (context, state) =>
          //           ProjectDetailPage(projectId: state.pathParameters['id']!),
          // ),
        ],
      ),
    ],
    redirect: (context, state) {
      final isLoggedin = authStatus.currentUser != null;
      final isLoggingIn = state.matchedLocation == LandingPage.route;
      if (!isLoggedin && !isLoggingIn) {
        return LandingPage.route;
      }
      if (isLoggedin && isLoggingIn) {
        return HomePage.route;
      }
      return null;
    },
    refreshListenable: GoRouterRefreshStream(authState),
  );
}

class GoRouterRefreshStream extends ChangeNotifier {
  GoRouterRefreshStream(Stream<User?> stream) {
    stream.listen((_) => notifyListeners());
  }
}
