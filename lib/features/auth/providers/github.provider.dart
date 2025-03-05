import 'package:commitz/features/auth/services/iauth.service.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers/global_providers.dart';
import '../services/github.service.dart';

final githubServiceProvider = Provider<IAuthService>((ref) {
  return GithubAuthService(
    auth: ref.read(firebaseAuthInstanceProvider),
    firestore: ref.read(firestoreInstanceProvider),
  );
});
