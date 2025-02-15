import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final firebaseAuthProvider = Provider<FirebaseAuth>((ref) {
  return FirebaseAuth.instance;
});

final firestoreProvider = Provider<FirebaseFirestore>((ref) {
  return FirebaseFirestore.instance;
});

final userSessionProvider = Provider((ref) {
  return FirebaseAuth.instance.currentUser;
});

final authStateProvider = StreamProvider<User?>((ref) {
  final authState = ref.watch(firebaseAuthProvider).authStateChanges();
  return authState;
});
