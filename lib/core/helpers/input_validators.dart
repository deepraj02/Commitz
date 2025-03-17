String? validateProjectName(String? value) {
  if (value == null || value.trim().isEmpty) {
    return 'Please enter a project name';
  }
  return null;
}

final RegExp _youtubeUrlPattern = RegExp(
  r'^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/.+$',
);
String? validateYoutubeUrl(String? value) {
  if (value == null || value.trim().isEmpty) {
    return 'Please enter a youtube URL';
  }

  if (!_youtubeUrlPattern.hasMatch(value)) {
    return 'Please enter a valid YouTube URL';
  }

  return null;
}
