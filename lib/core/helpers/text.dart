import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class CommitzText extends StatefulWidget {
  const CommitzText({
    super.key,
    required this.text,
    this.fontSize,
    this.fontWeight,
    this.color,
    this.gradient,
    this.textAlign,
  });

  CommitzText.gradient({
    super.key,
    required this.text,
    this.fontSize,
    this.textAlign,
    List<Color>? colors,
    this.fontWeight,
    this.color,
  }) : gradient = LinearGradient(
         begin: Alignment.topCenter,
         end: Alignment.bottomRight,
         colors:
             colors ?? [Colors.blueAccent, Colors.purpleAccent, Colors.amber],
       );

  final TextAlign? textAlign;
  final String text;
  final double? fontSize;
  final FontWeight? fontWeight;
  final Color? color;
  final LinearGradient? gradient;

  @override
  State<CommitzText> createState() => _CommitzTextState();
}

class _CommitzTextState extends State<CommitzText> {
  @override
  Widget build(BuildContext context) {
    return widget.gradient != null
        ? ShaderMask(
          shaderCallback: (Rect bounds) {
            return widget.gradient!.createShader(
              Rect.fromLTWH(0, 0, bounds.width, bounds.height),
            );
          },
          child: Text(
            textAlign: widget.textAlign ?? TextAlign.start,
            widget.text,
            style: GoogleFonts.sora(
              color: widget.color ?? Colors.white,
              fontSize: widget.fontSize,
              fontWeight: widget.fontWeight ?? FontWeight.normal,
            ),
          ),
        )
        : Text(
          textAlign: widget.textAlign ?? TextAlign.start,
          widget.text,
          style: GoogleFonts.sora(
            color: widget.color ?? Colors.white,
            fontSize: widget.fontSize,
            fontWeight: widget.fontWeight ?? FontWeight.normal,
          ),
        );
  }
}
