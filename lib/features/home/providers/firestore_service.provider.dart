import 'package:commitz/features/home/services/firestore.config.dart';
import 'package:fpdart/fpdart.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'firestore_service.provider.g.dart';

@riverpod
class FirestoreService extends _$FirestoreService {
  @override
  void build() {}

  Future<Either<Exception, String>> createEmptyProject(
    String projectName,
  ) async {
    final res = await ref
        .read(firestoreConfigProvider)
        .createMetadata(projectName);
    return res;
  }

  Future<void> addIssues(
    String userId,
    String projectId,
    List<Map<String, dynamic>> issues,
  ) async {
    final res = await ref
        .read(firestoreConfigProvider)
        .addIssuesToProject(userId, projectId, issues);
    return res;
  }
}
