import 'package:freezed_annotation/freezed_annotation.dart';


part 'gen/request.module.g.dart';
part 'gen/request.module.freezed.dart';

@freezed
sealed class RequestModel with _$RequestModel {
  factory RequestModel({
    required String id,
    required String projectName,
    required String projectVideoURL,
  }) = _RequestModel;
  
  factory RequestModel.fromJson(Map<String, dynamic> json) =>_$RequestModelFromJson(json);
}
