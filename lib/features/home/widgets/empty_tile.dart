import 'package:flutter/material.dart';

class EmptyTile extends StatelessWidget {
  const EmptyTile({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.blueGrey.withAlpha(4),
        borderRadius: BorderRadius.circular(8.0),
      ),
    );
  }
}
