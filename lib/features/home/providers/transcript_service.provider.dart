import 'package:commitz/features/home/state/home.state.dart';
import 'package:dio/dio.dart';
import 'package:fpdart/fpdart.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../services/video_transcript.service.dart';

part 'gen/transcript_service.provider.g.dart';

@riverpod
class VideoTranscript extends _$VideoTranscript {
  @override
  HomePageState build() {
    return HomePageStateInitial();
  }

  Future<Either<String, Map<String, dynamic>>> getTranscript(
    String videoUrl,
  ) async {
    state = HomePageStateLoading();
    final response = await ref
        .read(videoTranscriptServiceProvider)
        .post(
          "/transcript",
          options: Options(headers: {"X-Api-Key": "test_key"}),
          data: {"video_url": videoUrl},
        );
    state = HomePageStateInitial();
    return response.fold((error) => left(error), (data) => right(data));
  }
}
