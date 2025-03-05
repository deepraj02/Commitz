import 'package:commitz/features/error/pages/error.page.dart';
import 'package:commitz/features/home/pages/home.page.dart';
import 'package:commitz/features/project/pages/project.page.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../features/auth/pages/auth.page.dart';
import '../providers/global_providers.dart';

part 'app.router.g.dart';

@riverpod
GoRouter router(ref) {
  final navigatorKey = GlobalKey<NavigatorState>();
  final authStatus = ref.watch(firebaseAuthInstanceProvider);
  final authState = ref.watch(authStateProvider.stream);
  return GoRouter(
    navigatorKey: navigatorKey,
    debugLogDiagnostics: true,
    initialLocation: AuthPage.route,
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
            path: AuthPage.route,
            builder: (context, state) => AuthPage(),
          ),
          GoRoute(
            path: HomePage.route,
            builder: (context, state) => HomePage(),
          ),
          GoRoute(
            path: '/project',
            name: '/project',
            builder: (context, state) {
              final isLoggedin =
                  ref.read(firebaseAuthInstanceProvider).currentUser != null;
              if (!isLoggedin) {
                return AuthPage();
              }
              final projectid = state.uri.queryParameters['id'];
              return ProjectPage(id: projectid ?? "");
            },
          ),
        ],
      ),
    ],
    errorBuilder: (context, state) {
      return ErrorPage();
    },
    redirect: (context, state) {
      final isLoggedin = authStatus.currentUser != null;
      final isLoggingIn = state.matchedLocation == AuthPage.route;
      if (!isLoggedin && !isLoggingIn) {
        return AuthPage.route;
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
