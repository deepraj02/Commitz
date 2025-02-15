import 'package:commitz/app.dart';
import 'package:commitz/firebase_options.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_strategy/url_strategy.dart';

Future<void> main() async {
  setPathUrlStrategy();
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
  runApp(ProviderScope(child: const Commitz()));
}

// class MyApp extends StatelessWidget {
//   const MyApp({super.key});

//   @override
//   Widget build(BuildContext context) {
//     return MaterialApp(home: Scaffold(body: Commitz()));
//   }
// }

// class Commitz extends StatefulWidget {
//   const Commitz({super.key});

//   @override
//   State<Commitz> createState() => _CommitzState();
// }

// class _CommitzState extends State<Commitz> {
//   @override
//   Widget build(BuildContext context) {
//     return Column(
//       spacing: 30,
//       children: <Widget>[
//         Text('Commitz'),
//         Text('A simple app to track your daily commits'),
//         MaterialButton(
//           onPressed: () {
//             setState(() {
//               GithubAuthService(
//                 auth: FirebaseAuth.instance,
//                 firestore: FirebaseFirestore.instance,
//               ).signIn();
//             });
//           },
//           child: Text('Login with Github'),
//         ),
//       ],
//     );
//   }
// }
