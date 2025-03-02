// import 'package:cloud_firestore/cloud_firestore.dart';
// import 'package:firebase_auth/firebase_auth.dart';
// import 'package:flutter_riverpod/flutter_riverpod.dart';
// import 'package:uuid/uuid.dart';

// import '../models/issue.model.dart';
// import '../models/project.model.dart';

// class ProjectService {
//   final FirebaseFirestore _firestore;
//   final FirebaseAuth _auth;

//   ProjectService(this._firestore, this._auth);

//   Future<String> createProject(
//     String name,
//     String videoUrl,
//     List<IssueModel> issues,
//   ) async {
//     try {
//       final user = _auth.currentUser;
//       if (user == null) {
//         throw Exception('User not authenticated');
//       }

//       final projectId = const Uuid().v4();
//       final project = ProjectModel(
//         id: projectId,
//         name: name,
//         videoUrl: videoUrl,
//         issues: issues,
//         createdAt: DateTime.now(),
//       );

//       // Save to Firestore with efficient structure
//       await _firestore
//           .collection('users')
//           .doc(user.uid)
//           .collection('projects')
//           .doc(projectId)
//           .set(project.toJson()); // This line was missing the .set() call

//       return projectId;
//     } catch (e) {
//       throw Exception('Failed to create project: $e');
//     }
//   }

//   Stream<List<ProjectModel>> getUserProjects() {
//     final user = _auth.currentUser;
//     if (user == null) {
//       throw Exception('User not authenticated');
//     }

//     return _firestore
//         .collection('users')
//         .doc(user.uid)
//         .collection('projects')
//         .orderBy('created_at', descending: true)
//         .snapshots()
//         .map(
//           (snapshot) =>
//               snapshot.docs
//                   .map((doc) => ProjectModel.fromJson(doc.data()))
//                   .toList(),
//         );
//   }

//   Future<ProjectModel> getProject(String projectId) async {
//     final user = _auth.currentUser;
//     if (user == null) {
//       throw Exception('User not authenticated');
//     }

//     final doc =
//         await _firestore
//             .collection('users')
//             .doc(user.uid)
//             .collection('projects')
//             .doc(projectId)
//             .get();

//     if (!doc.exists) {
//       throw Exception('Project not found');
//     }

//     return ProjectModel.fromJson(doc.data()!);
//   }
// }

// final projectServiceProvider = Provider<ProjectService>((ref) {
//   return ProjectService(FirebaseFirestore.instance, FirebaseAuth.instance);
// });

// final userProjectsProvider = StreamProvider<List<ProjectModel>>((ref) {
//   return ref.watch(projectServiceProvider).getUserProjects();
// });

// final projectProvider = FutureProvider.family<ProjectModel, String>((
//   ref,
//   projectId,
// ) {
//   return ref.watch(projectServiceProvider).getProject(projectId);
// });
