import 'dart:developer';

import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:fpdart/fpdart.dart';

import 'iauth.service.dart';

class GithubAuthService implements IAuthService {
  final FirebaseAuth _auth;
  final FirebaseFirestore _firestore;

  GithubAuthService({
    required FirebaseAuth auth,
    required FirebaseFirestore firestore,
  }) : _auth = auth,
       _firestore = firestore;

  @override
  Future<Either<String, void>> logout() async {
    try {
      _auth.signOut();
      log("LOGOUT : ${_auth.currentUser}\n");
      return right(null);
    } catch (e) {
      log("LOGOUT ERROR : $e\n");
      return left(e.toString());
    }
  }

  @override
  Future<Either<String, User?>> signIn() async {
    GithubAuthProvider githubProvider = GithubAuthProvider();
    try {
      final UserCredential userCredential = await FirebaseAuth.instance
          .signInWithPopup(githubProvider);
      User? user = userCredential.user;
      if (user != null) {
        if (userCredential.additionalUserInfo!.isNewUser) {
          await _firestore.collection('users').doc(user.uid).set({
            'email': user.email,
            'name': user.displayName,
            'photoUrl': user.photoURL,
            'createdAt': Timestamp.now(),
          });
        }
      }
      return right(user!);
    } on FirebaseAuthException catch (e) {
      log(e.message.toString());
      return left("Error: ${e.message}");
    }
  }
}
