import 'dart:developer';

import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fpdart/fpdart.dart';
import 'package:uuid/uuid.dart';

import '../../../core/providers/global_providers.dart';

class FirestoreService {
  final FirebaseAuth _auth;
  final FirebaseFirestore _firestore;

  FirestoreService({
    required FirebaseAuth auth,
    required FirebaseFirestore firestore,
  }) : _auth = auth,
       _firestore = firestore;

  final uuid = Uuid();
  // Future<Either<Exception, String>> createMetadata(String projectName) async {
  //   try {
  //     final user = _auth.currentUser;
  //     if (user == null) {
  //       throw Exception('User not authenticated');
  //     }

  //     final projectId = uuid.v4();

  //     // First check if the user document exists
  //     final userDoc = await _firestore.collection('users').doc(user.uid).get();

  //     if (userDoc.exists) {
  //       // Get the current user data
  //       //! Create a new Project
  //       await _firestore.collection('users').doc(user.uid).update({
  //         "Projectsv3": FieldValue.arrayUnion([
  //           {
  //             "name": projectName,
  //             "project_id": projectId,
  //             "issues": [
  //               {"title": "Issue 1", "description": "This is the first issue"},
  //             ],
  //           },
  //         ]),
  //       });

  //       // await _firestore.collection('users').doc(user.uid).get("");
  //     } else {
  //       // Create new document
  //       await _firestore.collection('users').doc(user.uid).set({
  //         "Projectsv3": [
  //           {
  //             "name": projectName,
  //             "project_id": projectId,
  //             "issues": [
  //               {"title": "Issue 1", "description": "This is the first issue"},
  //             ],
  //           },
  //         ],
  //       });
  //     }

  //     return right(projectId);
  //   } catch (e) {
  //     return left(Exception('Failed to create metadata: $e'));
  //   }
  // }

  // Future<Either<Exception, String>> createMetadata(String projectName) async {
  //   try {
  //     final user = _auth.currentUser;
  //     if (user == null) {
  //       throw Exception('User not authenticated');
  //     }

  //     final projectId = uuid.v4();
  //     final userDoc = await _firestore.collection('users').doc(user.uid).get();

  //     if (userDoc.exists) {
  //       await _firestore.collection('users').doc(user.uid).update({
  //         "Projectsv3": FieldValue.arrayUnion([
  //           {
  //             "name": projectName,
  //             "project_id": projectId,
  //             "issues": [], // Start with empty issues array
  //           },
  //         ]),
  //       });
  //     } else {
  //       await _firestore.collection('users').doc(user.uid).set({
  //         "Projectsv3": [
  //           {
  //             "name": projectName,
  //             "project_id": projectId,
  //             "issues": [], // Start with empty issues array
  //           },
  //         ],
  //       });
  //     }

  //     return right(projectId);
  //   } catch (e) {
  //     return left(Exception('Failed to create metadata: $e'));
  //   }
  // }

  Future<Either<Exception, String>> createMetadata(String projectName) async {
    try {
      final user = _auth.currentUser;
      if (user == null) {
        throw Exception('User not authenticated');
      }

      final projectId = uuid.v4();
      final userDoc = await _firestore.collection('users').doc(user.uid).get();
      final timestamp = DateTime.now().millisecondsSinceEpoch;

      if (userDoc.exists) {
        await _firestore.collection('users').doc(user.uid).update({
          "Projectsv3": FieldValue.arrayUnion([
            {
              "name": projectName,
              "project_id": projectId,
              "created_at": timestamp, // Add timestamp
              "issues": [], // Start with empty issues array
            },
          ]),
        });
      } else {
        await _firestore.collection('users').doc(user.uid).set({
          "Projectsv3": [
            {
              "name": projectName,
              "project_id": projectId,
              "created_at": timestamp, // Add timestamp
              "issues": [], // Start with empty issues array
            },
          ],
        });
      }

      return right(projectId);
    } catch (e) {
      return left(Exception('Failed to create metadata: $e'));
    }
  }

  Future<void> addIssuesToProject(
    String userId,
    String projectId,
    List<Map<String, dynamic>> issues,
  ) async {
    try {
      DocumentReference userDocRef = _firestore.collection('users').doc(userId);
      DocumentSnapshot userDoc = await userDocRef.get();

      if (userDoc.exists) {
        Map<String, dynamic> userData = userDoc.data() as Map<String, dynamic>;
        List<dynamic> projectsv3 = List.from(userData['Projectsv3'] ?? []);

        int projectIndex = -1;
        for (int i = 0; i < projectsv3.length; i++) {
          if (projectsv3[i]['project_id'] == projectId) {
            projectIndex = i;
            break;
          }
        }

        if (projectIndex != -1) {
          Map<String, dynamic> project = Map<String, dynamic>.from(
            projectsv3[projectIndex],
          );

          if (!project.containsKey('issues') || project['issues'] == null) {
            project['issues'] = [];
          }

          List<dynamic> existingIssues = List.from(project['issues']);
          existingIssues.addAll(issues);

          project['issues'] = existingIssues;
          projectsv3[projectIndex] = project;

          await userDocRef.update({'Projectsv3': projectsv3});
          log('Added ${issues.length} issues to project $projectId');
        }
      }
    } catch (e) {
      log('Error adding issues: $e');
      rethrow;
    }
  }
}

final firestoreProvider = Provider<FirestoreService>((ref) {
  return FirestoreService(
    auth: ref.read(firebaseAuthInstanceProvider),
    firestore: ref.read(firestoreInstanceProvider),
  );
});
