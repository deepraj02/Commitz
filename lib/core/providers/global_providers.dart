import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final firebaseAuthInstanceProvider = Provider<FirebaseAuth>((ref) {
  return FirebaseAuth.instance;
});

final firestoreInstanceProvider = Provider<FirebaseFirestore>((ref) {
  return FirebaseFirestore.instance;
});

final userSessionInstanceProvider = Provider((ref) {
  return FirebaseAuth.instance.currentUser;
});

final authStateProvider = StreamProvider<User?>((ref) {
  final authState = ref.watch(firebaseAuthInstanceProvider).authStateChanges();
  return authState;
});
