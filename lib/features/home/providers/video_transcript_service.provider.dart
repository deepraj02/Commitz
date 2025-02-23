import 'package:commitz/features/home/state/home.state.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'gen/video_transcript_service.provider.g.dart';

@riverpod
class VideoTranscriptService extends _$VideoTranscriptService {
  @override
  HomePageState build() {
    return HomePageStateInitial();
  }

  
  
}
