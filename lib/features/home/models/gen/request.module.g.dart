// GENERATED CODE - DO NOT MODIFY BY HAND

part of '../request.module.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_RequestModel _$RequestModelFromJson(Map<String, dynamic> json) =>
    _RequestModel(
      id: json['id'] as String,
      projectName: json['projectName'] as String,
      projectVideoURL: json['projectVideoURL'] as String,
    );

Map<String, dynamic> _$RequestModelToJson(_RequestModel instance) =>
    <String, dynamic>{
      'id': instance.id,
      'projectName': instance.projectName,
      'projectVideoURL': instance.projectVideoURL,
    };
