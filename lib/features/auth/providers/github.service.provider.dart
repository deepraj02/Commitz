import 'package:commitz/core/providers/global_providers.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../state/auth.state.dart';
import 'github.provider.dart';

part 'github.service.provider.g.dart';

@riverpod
class GithubAuth extends _$GithubAuth {
  @override
  AuthState build() {
    init();
    return AuthStateLoading();
  }

  Future<void> signInWithGithub() async {
    state = AuthStateLoading();
    final response = await ref.read(githubServiceProvider).signIn();
    state = response.fold(
      (error) => AuthStateFailure(error),
      (user) => AuthStateSuccess(user: user!),
    );
  }

  Future<void> signOut() async {
    state = AuthStateLoading();
    final response = await ref.read(githubServiceProvider).logout();
    state = response.fold(
      (error) => AuthStateFailure(error),
      (_) => AuthStateInitial(),
    );
  }

  Future<void> init() async {
    final userSession = ref.read(userSessionProvider);
    if (userSession != null) {
      state = AuthStateSuccess(user: userSession);
    } else {
      state = AuthStateInitial();
    }
  }
}
