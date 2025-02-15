import 'package:firebase_auth/firebase_auth.dart';
import 'package:fpdart/fpdart.dart';

abstract interface class IAuthService {
  Future<Either<String, void>> logout();
  Future<Either<String, User?>> signIn();
}
