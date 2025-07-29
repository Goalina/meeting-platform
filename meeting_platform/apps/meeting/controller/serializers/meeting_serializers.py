#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/8/16 17:08
# @Author  : Tom_zc
# @FileName: meeting_serializers.py
# @Software: PyCharm

import logging
import math
from datetime import datetime

from django.conf import settings
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from meeting.models import Meeting, MeetingObsRecords, MeetingCycleDate
from meeting.infrastructure.dao.meeting_cycle_sub_dao import MeetingCycleSubMeetingDao

from meeting_platform.utils.check_params import check_field, check_invalid_content, check_email_list, check_date, \
    check_time, check_link, check_duration
from meeting_platform.utils.common import mask_email_full
from meeting_platform.utils.ret_api import MyValidationError
from meeting_platform.utils.ret_code import RetCode
from meeting_platform.utils.client.audit_client import AuditClient

logger = logging.getLogger("log")


# noinspection PyMethodMayBeStatic
class MeetingSerializer(ModelSerializer):
    """MeetingSerializer for get a meeting and create meeting"""
    __audit_client = AuditClient()
    __cycle_sub_dao = MeetingCycleSubMeetingDao()

    duration = serializers.SerializerMethodField()
    duration_time = serializers.SerializerMethodField()
    bili_status = serializers.SerializerMethodField()
    bili_replay_url = serializers.SerializerMethodField()
    translate_status = serializers.SerializerMethodField()
    text_vtt_url = serializers.SerializerMethodField()
    text_json_url = serializers.SerializerMethodField()
    text_video_url = serializers.SerializerMethodField()
    cycle_start_date = serializers.SerializerMethodField()
    cycle_end_date = serializers.SerializerMethodField()
    cycle_start = serializers.SerializerMethodField()
    cycle_end = serializers.SerializerMethodField()
    cycle_type = serializers.SerializerMethodField()
    cycle_interval = serializers.SerializerMethodField()
    cycle_point = serializers.SerializerMethodField()
    cycle_sub = serializers.SerializerMethodField()

    class Meta:
        """Meta Meta"""
        model = Meeting
        fields = ['id', 'sponsor', 'group_name', 'community', 'topic', 'platform', 'date', 'start', 'end',
                  'agenda', 'etherpad', 'email_list', 'mid', 'm_mid', 'join_url', 'create_time', 'update_time',
                  'is_delete', 'is_record', 'bili_status', 'bili_replay_url', 'translate_status', 'text_vtt_url',
                  'text_json_url', 'text_video_url', 'duration', 'duration_time', 'is_cycle', 'cycle_start_date',
                  'cycle_end_date', 'cycle_start', 'cycle_end', 'cycle_type', 'cycle_interval', 'cycle_point',
                  'cycle_sub']
        extra_kwargs = {
            'id': {'read_only': True},
            'sponsor': {'required': True},
            'group_name': {'required': True},
            'community': {'required': True},
            'topic': {'required': True},
            'platform': {'required': True},
            'date': {'required': True},
            'start': {'required': True},
            'end': {'required': True},
            'agenda': {'required': False},
            'etherpad': {'required': False},
            'email_list': {'required': False},
            'is_record': {'required': True},
            'mid': {'read_only': True},
            'm_mid': {'read_only': True},
            'join_url': {'read_only': True},
            'bili_status': {'read_only': True},
            'bili_replay_url': {'read_only': True},
            'translate_status': {'read_only': True},
            'text_vtt_url': {'read_only': True},
            'text_json_url': {'read_only': True},
            'text_video_url': {'read_only': True},
            'create_time': {'read_only': True},
            'update_time': {'read_only': True},
            'is_delete': {'read_only': True},
            'duration': {'read_only': True},
            'duration_time': {'read_only': True},
            'is_cycle': {'required': True},
            'cycle_start_date': {'required': False},
            'cycle_end_date': {'required': False},
            'cycle_start': {'required': False},
            'cycle_end': {'required': False},
            'cycle_type': {'required': False},
            'cycle_interval': {'required': False},
            'cycle_point': {'required': False},
            'cycle_sub': {'read_only': True},
        }

    def _check_content_by_audit(self, value):
        if value:
            if not self.__audit_client.check_content_ok(value):
                raise MyValidationError(RetCode.STATUS_INVALID_CONTENT_FAILED)

    def validate_sponsor(self, value):
        """check length of 64"""
        check_field(value, 64)
        check_invalid_content(value)
        self._check_content_by_audit(value)
        return value

    def validate_group_name(self, value):
        """check length of 64"""
        check_field(value, 64)
        check_invalid_content(value)
        self._check_content_by_audit(value)
        return value

    def validate_community(self, value):
        """check community"""
        if value not in settings.COMMUNITY_SUPPORT:
            logger.error("community {} is not exist in COMMUNITY_SUPPORT".format(value))
            raise MyValidationError(RetCode.STATUS_PARAMETER_ERROR)
        return value

    def validate_topic(self, value):
        """check length of 128，not include \r\n url xss"""
        check_field(value, 128)
        check_invalid_content(value)
        self._check_content_by_audit(value)
        return value

    def validate_platform(self, value):
        """check platform"""
        return value

    def validate_date(self, value):
        """check date"""
        value = check_date(value)
        return value.strftime('%Y-%m-%d')

    @staticmethod
    def check_date(value):
        value = check_date(value)
        return value.strftime('%Y-%m-%d')

    def validate_start(self, value):
        """check start"""
        check_time(value)
        return value

    def validate_end(self, value):
        """check end"""
        check_time(value)
        return value

    def validate_is_record(self, value):
        """check record"""
        if not isinstance(value, bool):
            logger.error("invalid is_record:{}".format(value))
            raise MyValidationError(RetCode.STATUS_PARAMETER_ERROR)
        return value

    def validate_etherpad(self, value):
        """check etherpad"""
        if value:
            check_link(value)
            return value

    def validate_agenda(self, value):
        """check agenda"""
        if value:
            check_field(value, 4096)
            check_invalid_content(value, check_crlf=False)
            self._check_content_by_audit(value)
            return value

    def validate_email_list(self, value):
        """check email_list"""
        if value:
            check_email_list(value)
            return value

    def validate(self, attrs):
        check_duration(attrs["start"], attrs["end"], attrs["date"], datetime.now())
        if attrs["community"] not in settings.COMMUNITY_HOST.keys():
            logger.error('the community of {} have no resources in COMMUNITY_HOST in settings.'
                         .format(attrs["community"]))
            raise MyValidationError(RetCode.STATUS_PARAMETER_ERROR)
        if attrs["platform"] not in settings.COMMUNITY_HOST[attrs["community"]].keys():
            logger.error('platform {} is not exist in COMMUNITY_HOST.'.format(attrs["platform"]))
            raise MyValidationError(RetCode.STATUS_PARAMETER_ERROR)
        return attrs

    def get_bili_status(self, obj):
        if obj.bili_record:
            return obj.bili_record.status

    def get_bili_replay_url(self, obj):
        if obj.bili_record:
            return obj.bili_record.replay_url

    def get_translate_status(self, obj):
        if obj.obs_records:
            return obj.obs_records.status

    def get_text_vtt_url(self, obj):
        if obj.obs_records:
            return obj.obs_records.text_vtt_url

    def get_text_json_url(self, obj):
        if obj.obs_records:
            return obj.obs_records.text_json_url

    def get_text_video_url(self, obj):
        if obj.obs_records:
            return obj.obs_records.text_video_url

    def get_duration(self, obj):
        """get duration"""
        return math.ceil(float(obj.end.replace(':', '.'))) - math.floor(float(obj.start.replace(':', '.')))

    def get_duration_time(self, obj):
        """get duration time"""
        return obj.start.split(':')[0] + ':00' + '-' + str(math.ceil(float(obj.end.replace(':', '.')))) + ':00'

    def get_cycle_start_date(self, obj):
        """get cycle start date, and eg:2025-08-00"""
        if obj.cycle_date:
            return obj.cycle_date.start_date

    def get_cycle_end_date(self, obj):
        """get cycle end date, and eg:2025-08-30"""
        if obj.cycle_date:
            return obj.cycle_date.end_date

    def get_cycle_start(self, obj):
        """get cycle end date, and eg:08:00"""
        if obj.cycle_date:
            return obj.cycle_date.start

    def get_cycle_end(self, obj):
        """get cycle end date, and eg:09:00"""
        if obj.cycle_date:
            return obj.cycle_date.end

    def get_cycle_type(self, obj):
        """get cycle type, and eg:"""
        if obj.cycle_date:
            return obj.cycle_date.cycle_type

    def get_cycle_interval(self, obj):
        """get cycle interval"""
        if obj.cycle_date:
            return obj.cycle_date.interval

    def get_cycle_point(self, obj):
        """get cycle point"""
        if obj.cycle_date:
            return obj.cycle_date.point

    def get_cycle_sub(self, obj):
        """get cycle point"""
        if obj.cycle_date:
            return self.__cycle_sub_dao.get_by_mid(obj.mid)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["email_list"] = self._to_anonymous_email_list(data.get("email_list"))
        return data

    def _to_anonymous_email_list(self, email_list):
        """get email list"""
        if email_list:
            email_strs = email_list.split(";")
            desensitization_email = [mask_email_full(email) for email in email_strs]
            return ";".join(desensitization_email)
        return email_list


# noinspection PyMethodMayBeStatic
class SingleMeetingSerializer(ModelSerializer):
    """UpdateMeetingSerializer for update meeting"""
    __audit_client = AuditClient()
    __cycle_sub_dao = MeetingCycleSubMeetingDao()

    duration = serializers.SerializerMethodField()
    duration_time = serializers.SerializerMethodField()
    email_list = serializers.SerializerMethodField()
    bili_status = serializers.SerializerMethodField()
    bili_replay_url = serializers.SerializerMethodField()
    translate_status = serializers.SerializerMethodField()
    text_vtt_url = serializers.SerializerMethodField()
    text_json_url = serializers.SerializerMethodField()
    text_video_url = serializers.SerializerMethodField()
    cycle_start_date = serializers.SerializerMethodField()
    cycle_end_date = serializers.SerializerMethodField()
    cycle_start = serializers.SerializerMethodField()
    cycle_end = serializers.SerializerMethodField()
    cycle_type = serializers.SerializerMethodField()
    cycle_interval = serializers.SerializerMethodField()
    cycle_point = serializers.SerializerMethodField()
    cycle_sub = serializers.SerializerMethodField()

    class Meta:
        """Meta Meta"""
        model = Meeting
        fields = ['id', 'sponsor', 'group_name', 'community', 'topic', 'platform', 'date', 'start', 'end',
                  'agenda', 'etherpad', 'email_list', 'mid', 'm_mid', 'is_record', 'duration', 'duration_time',
                  'bili_status', 'bili_replay_url', 'translate_status', 'text_vtt_url', 'text_json_url',
                  'text_video_url', 'join_url', 'create_time', 'update_time', 'is_delete',
                  'is_cycle', 'cycle_start_date', 'cycle_end_date', 'cycle_start', 'cycle_end', 'cycle_type',
                  'cycle_interval', 'cycle_point', 'cycle_sub']
        extra_kwargs = {
            'id': {'read_only': True},
            'sponsor': {'read_only': True},
            'group_name': {'read_only': True},
            'community': {'read_only': True},
            'platform': {'read_only': True},
            'topic': {'required': True},
            'date': {'required': True},
            'start': {'required': True},
            'end': {'required': True},
            'agenda': {'required': False},
            'etherpad': {'required': False},
            'is_record': {'required': True},
            'email_list': {'read_only': True},
            'mid': {'read_only': True},
            'm_mid': {'read_only': True},
            'join_url': {'read_only': True},
            'bili_status': {'read_only': True},
            'bili_replay_url': {'read_only': True},
            'translate_status': {'read_only': True},
            'text_vtt_url': {'read_only': True},
            'text_json_url': {'read_only': True},
            'text_video_url': {'read_only': True},
            'create_time': {'read_only': True},
            'update_time': {'read_only': True},
            'is_delete': {'read_only': True},
            'duration': {'read_only': True},
            'duration_time': {'read_only': True},
            'is_cycle': {'required': True},
            'cycle_start_date': {'read_only': True},
            'cycle_end_date': {'read_only': True},
            'cycle_start': {'read_only': True},
            'cycle_end': {'read_only': True},
            'cycle_type': {'read_only': True},
            'cycle_interval': {'read_only': True},
            'cycle_point': {'read_only': True},
            'cycle_sub': {'read_only': True},
        }

    def _check_content_by_audit(self, value):
        if value:
            if not self.__audit_client.check_content_ok(value):
                raise MyValidationError(RetCode.STATUS_INVALID_CONTENT_FAILED)

    def validate_topic(self, value):
        """check length of 128，not include \r\n url xss"""
        check_field(value, 128)
        check_invalid_content(value)
        self._check_content_by_audit(value)
        return value

    def validate_date(self, value):
        """check date"""
        value = check_date(value)
        return value.strftime('%Y-%m-%d')

    def validate_start(self, value):
        """check start"""
        check_time(value)
        return value

    def validate_end(self, value):
        """check end"""
        check_time(value)
        return value

    def validate_agenda(self, value):
        """check agenda"""
        if value:
            check_field(value, 4096)
            check_invalid_content(value, check_crlf=False)
            self._check_content_by_audit(value)
            return value

    def validate_etherpad(self, value):
        """check etherpad"""
        if value:
            check_link(value)
            return value

    def validate_is_record(self, value):
        """check record"""
        if not isinstance(value, bool):
            logger.error("invalid is_record:{}".format(value))
            raise MyValidationError(RetCode.STATUS_PARAMETER_ERROR)
        return value

    def validate(self, attrs):
        """all validate data"""
        check_duration(attrs["start"], attrs["end"], attrs["date"], datetime.now())
        attrs["update_time"] = datetime.now()
        return attrs

    def get_bili_status(self, obj):
        if obj.bili_record:
            return obj.bili_record.status

    def get_bili_replay_url(self, obj):
        if obj.bili_record:
            return obj.bili_record.replay_url

    def get_translate_status(self, obj):
        if obj.obs_records:
            return obj.obs_records.status

    def get_text_vtt_url(self, obj):
        if obj.obs_records:
            return obj.obs_records.text_vtt_url

    def get_text_json_url(self, obj):
        if obj.obs_records:
            return obj.obs_records.text_json_url

    def get_text_video_url(self, obj):
        if obj.obs_records:
            return obj.obs_records.text_video_url

    def get_duration(self, obj):
        """get duration"""
        return math.ceil(float(obj.end.replace(':', '.'))) - math.floor(float(obj.start.replace(':', '.')))

    def get_duration_time(self, obj):
        """get duration time"""
        return obj.start.split(':')[0] + ':00' + '-' + str(math.ceil(float(obj.end.replace(':', '.')))) + ':00'

    def get_cycle_start_date(self, obj):
        """get cycle start date"""
        if obj.cycle_date:
            return obj.cycle_date.start_date

    def get_cycle_end_date(self, obj):
        """get cycle end date"""
        if obj.cycle_date:
            return obj.cycle_date.end_date

    def get_cycle_start(self, obj):
        """get cycle end date"""
        if obj.cycle_date:
            return obj.cycle_date.start

    def get_cycle_end(self, obj):
        """get cycle end date"""
        if obj.cycle_date:
            return obj.cycle_date.end

    def get_cycle_type(self, obj):
        """get cycle end date"""
        if obj.cycle_date:
            return obj.cycle_date.cycle_type

    def get_cycle_interval(self, obj):
        """get cycle end date"""
        if obj.cycle_date:
            return obj.cycle_date.interval

    def get_cycle_point(self, obj):
        """get cycle end date"""
        if obj.cycle_date:
            return obj.cycle_date.point

    def get_cycle_sub(self, obj):
        """get cycle point"""
        if obj.cycle_date:
            return self.__cycle_sub_dao.get_by_mid(obj.mid)

    def get_email_list(self, obj):
        """get email list"""
        email_list = obj.email_list
        if email_list:
            email_strs = email_list.split(";")
            desensitization_email = [mask_email_full(email) for email in email_strs]
            return ";".join(desensitization_email)
        return email_list


# noinspection PyMethodMayBeStatic
class CycleDateSerializer(ModelSerializer):
    __cycle_sub_dao = MeetingCycleSubMeetingDao()

    cycle_sub = serializers.SerializerMethodField()

    class Meta:
        model = MeetingCycleDate
        fields = ['mid', 'sub_id', 'date', 'start', 'end', "is_record"]
        extra_kwargs = {
            'mid': {'required': True},
            'sub_id': {'required': True},
            'date': {'required': True},
            'start': {'required': True},
            'end': {'required': True},
            'is_record': {'required': True}
        }

    def get_cycle_sub(self, obj):
        """get cycle point"""
        return self.__cycle_sub_dao.get_by_mid(obj.mid)


# noinspection PyMethodMayBeStatic
class TranslateVideoTextSerializer(ModelSerializer):
    class Meta:
        model = MeetingObsRecords
        fields = ['mid', 'text_vtt_url', 'text_json_url', 'text_video_url']

    def validate_mid(self, value):
        if not value:
            logger.error("check the empty mid")
            raise MyValidationError(RetCode.STATUS_PARAMETER_ERROR)
        return value

    def validate_text_vtt_url(self, value):
        if not value:
            logger.error("check the empty text_vtt_url")
            raise MyValidationError(RetCode.STATUS_PARAMETER_ERROR)
        return value

    def validate_text_json_url(self, value):
        if not value:
            logger.error("check the empty text_json_url")
            raise MyValidationError(RetCode.STATUS_PARAMETER_ERROR)
        return value
