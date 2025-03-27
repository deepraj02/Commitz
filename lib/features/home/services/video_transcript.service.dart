// ignore: constant_identifier_names
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fpdart/fpdart.dart';

class VideoTransriptService {
  VideoTransriptService._();
  static final instance = VideoTransriptService._();
  static final String baseUrl = "http://localhost:9000/api/v1";
  final Dio _dio = Dio(
    BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 60),
      receiveTimeout: const Duration(seconds: 60),
      responseType: ResponseType.json,
    ),
  );

  Future<Either<String, Map<String, dynamic>>> post(
    String path, {
    data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
    ProgressCallback? onSendProgress,
    ProgressCallback? onReceiveProgress,
  }) async {
    try {
      final Response response = await _dio.post(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
        cancelToken: cancelToken,
        onSendProgress: onSendProgress,
        onReceiveProgress: onReceiveProgress,
      );
      if (response.statusCode == 200 || response.statusCode == 201) {
        return Right(response.data);
      }
      return Left("something went wrong");
    } catch (e) {
      return Left(e.toString());
    }
  }
}

final videoTranscriptServiceProvider = Provider<VideoTransriptService>((ref) {
  return VideoTransriptService.instance;
});
