#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/8/16 14:59
# @Author  : Tom_zc
# @FileName: meeting.py
# @Software: PyCharm
import datetime
import logging
import secrets
import traceback

from django.conf import settings
from django.utils import timezone
from django.forms import model_to_dict
from django.db.models import Q
from django.db import transaction

from meeting.domain.primitive.upload_status import UploadStatus
from meeting_platform.utils.common import start_thread, get_cur_date
from meeting_platform.utils.operation_log import set_log_thread_local, log_key
from meeting_platform.utils.ret_api import MyValidationError
from meeting_platform.utils.ret_code import RetCode
from meeting.infrastructure.adapter.meeting_adapter_impl.meeting_adapter_impl import MeetingAdapterImpl
from meeting.infrastructure.dao import meeting_dao, meeting_participants_dao
from meeting.domain.primitive.time_range import TimeRange
from meeting.infrastructure.adapter.message_adapter_impl.email_adapter_impl import CreateMessageEmailAdapterImpl, \
    DeleteMessageEmailAdapterImpl, UpdateMessageEmailAdapterImpl
from meeting.infrastructure.adapter.message_adapter_impl.kafka_adapter_impl import CreateMessageKafKaAdapterImpl, \
    DeleteMessageKafKaAdapterImpl, UpdateMessageKafKaAdapterImpl
from meeting.infrastructure.dao.meeting_records_obs_dao import MeetingRecordsObsDao
from meeting.infrastructure.dao.meeting_records_bili_dao import MeetingRecordsBiliDao

logger = logging.getLogger("log")


class MeetingApp:
    meeting_dao = meeting_dao.MeetingDao
    meeting_obs_records_dao = MeetingRecordsObsDao
    meeting_bili_records_dao = MeetingRecordsBiliDao
    meeting_participants_dao = meeting_participants_dao.MeetingParticipantsDao
    meeting_adapter_impl = MeetingAdapterImpl()
    create_message_adapter_impl = [CreateMessageEmailAdapterImpl, CreateMessageKafKaAdapterImpl]
    update_message_adapter_impl = [UpdateMessageEmailAdapterImpl, UpdateMessageKafKaAdapterImpl]
    delete_message_adapter_impl = [DeleteMessageEmailAdapterImpl, DeleteMessageKafKaAdapterImpl]

    def _get_and_check_conflict_meetings_by_date(self, meeting, meeting_id=None):
        """check the conflict the meeting, if not conflict and return meeting"""
        community = meeting["community"]
        platform = meeting["platform"]
        date = meeting["date"]
        start = meeting["start"]
        end = meeting["end"]
        start_search = datetime.datetime.strftime(
            (datetime.datetime.strptime(start, '%H:%M') - datetime.timedelta(minutes=30)),
            '%H:%M')
        end_search = datetime.datetime.strftime(
            (datetime.datetime.strptime(end, '%H:%M') + datetime.timedelta(minutes=30)),
            '%H:%M')
        meetings = self.meeting_dao.get_conflict_meeting(community, platform, date,
                                                         start_search, end_search, meeting_id).values()
        unavailable_host_ids = [meeting['host_id'] for meeting in meetings]
        host_info = settings.COMMUNITY_HOST[meeting["community"]][meeting["platform"]]
        host_list = [key["HOST"] for key in host_info]
        available_host_id = list(set(host_list) - set(unavailable_host_ids))
        if len(available_host_id) == 0:
            logger.info('[MeetingApp/_get_and_check_conflict_meetings_by_date] '
                        '{}/{}: no available host'.format(meeting["community"], meeting["platform"]))
            raise MyValidationError(RetCode.STATUS_MEETING_DATE_CONFLICT)
        return available_host_id

    @staticmethod
    def _is_in_prepare_meeting_duration_before_meeting(meeting):
        start_date_str = "{} {}".format(meeting["date"], meeting["start"])
        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d %H:%M")
        if int((start_date - get_cur_date()).total_seconds()) < 0:
            raise MyValidationError(RetCode.STATUS_MEETING_CANNOT_BE_OPERATE_BY_EXPIRED)
        if int((start_date - get_cur_date()).total_seconds()) < 60 * 60:
            raise MyValidationError(RetCode.STATUS_MEETING_CANNOT_BE_OPERATE)

    @staticmethod
    def _send_message(meeting, message_handler):
        """send the message"""
        for handler in message_handler:
            try:
                handler().send_message(meeting)
            except Exception as e:
                logger.error("[MeetingApp/_send_message] err:{}, and traceback:{}".format(e, traceback.format_exc()))

    def _calc_meeting_count(self, meeting):
        today = timezone.now().date()
        meeting_counts = self.meeting_dao.get_today_meeting_counts(meeting["community"], meeting["sponsor"], today)
        if meeting_counts >= settings.MEETING_CREATE_COUNT:
            raise MyValidationError(RetCode.STATUS_MEETING_CREATE_COUNT_LIMIT)

    def _check_recurring_meetings(self, meeting):
        m_count = self.meeting_dao.get_repeat_meeting_by_community_sponsor_date_start_counts(meeting["community"],
                                                                                             meeting["group_name"],
                                                                                             meeting["sponsor"],
                                                                                             meeting["date"],
                                                                                             meeting["start"])
        if m_count != 0:
            raise MyValidationError(RetCode.STATUS_MEETING_REPEAT_FAILED)

    def _save_dao(self, meeting):
        with transaction.atomic():
            if meeting["is_record"]:
                obs_record_obj = self.meeting_obs_records_dao.create(UploadStatus.INIT.value, meeting["mid"])
                meeting["obs_records"] = obs_record_obj
                bili_record_obj = self.meeting_bili_records_dao.create(UploadStatus.INIT.value, meeting["mid"])
                meeting["bili_record"] = bili_record_obj
            else:
                meeting["obs_records"] = None
                meeting["bili_record"] = None
            return self.meeting_dao.create(**meeting)

    def _update_dao(self, meeting_id, meeting):
        with transaction.atomic():
            obs_record_obj = self.meeting_obs_records_dao.get_by_mid(meeting["mid"])
            bili_record_obj = self.meeting_bili_records_dao.get_by_mid(meeting["mid"])
            if meeting["is_record"]:
                if not obs_record_obj:
                    obs_record_obj = self.meeting_obs_records_dao.create(UploadStatus.INIT.value, meeting["mid"])
                meeting["obs_records"] = obs_record_obj
                if not bili_record_obj:
                    bili_record_obj = self.meeting_bili_records_dao.create(UploadStatus.INIT.value, meeting["mid"])
                meeting["bili_record"] = bili_record_obj
            else:
                if obs_record_obj:
                    self.meeting_obs_records_dao.delete_by_mid(meeting["mid"])
                    meeting["obs_records"] = None
                if bili_record_obj:
                    self.meeting_bili_records_dao.delete_by_mid(meeting["mid"])
                    meeting["bili_record"] = None
            return self.meeting_dao.update_by_id(meeting_id, **meeting)

    def _delete_dao(self, meeting_id):
        with transaction.atomic():
            meeting_obj = self.meeting_dao.get_by_id(meeting_id)
            self.meeting_bili_records_dao.delete_by_mid(meeting_obj.mid)
            self.meeting_obs_records_dao.delete_by_mid(meeting_obj.mid)
            return self.meeting_dao.delete_by_id(meeting_id)

    def create(self, meeting):
        """create meeting"""
        # check the meeting limit
        self._calc_meeting_count(meeting)
        # check the recurring meetings
        self._check_recurring_meetings(meeting)
        # check meeting-conflict
        available_host_id = self._get_and_check_conflict_meetings_by_date(meeting)
        meeting["host_id"] = secrets.choice(available_host_id)
        # create meeting
        meeting["mid"], meeting["m_mid"], meeting["join_url"] = self.meeting_adapter_impl.create(meeting["host_id"],
                                                                                                 meeting)
        # create in database
        result = self._save_dao(meeting)
        meeting["id"] = result.id
        # send message
        start_thread(self._send_message, (meeting, self.create_message_adapter_impl))
        logger.info('[MeetingApp/create] {}/{}: create meeting which mid is {} and id is {}.'.
                    format(meeting["community"], meeting["platform"], meeting["mid"], result))
        return meeting["id"]

    def update(self, request, meeting_id, meeting_data):
        """update meeting"""
        meeting = self.meeting_dao.get_by_id(meeting_id)
        if not meeting:
            logger.error('[MeetingApp/update]Invalid meeting id:{}'.format(meeting_id))
            raise MyValidationError(RetCode.INFORMATION_CHANGE_ERROR)
        meeting = model_to_dict(meeting)
        set_log_thread_local(request, log_key, [meeting["community"], meeting["topic"], meeting_id])
        meeting.update(meeting_data)
        meeting.update({"sequence": meeting["sequence"] + 1})
        # check modify meeting count
        if meeting["sequence"] > settings.MEETING_MODIFY_COUNT + 1:
            raise MyValidationError(RetCode.STATUS_MEETING_MODIFY_COUNT_LIMIT)
        # check meeting-conflict
        self._get_and_check_conflict_meetings_by_date(meeting, meeting_id)
        # check not update in the before in start date
        self._is_in_prepare_meeting_duration_before_meeting(meeting)
        # update meeting
        self.meeting_adapter_impl.update(meeting)
        # update in database
        result = self._update_dao(meeting_id, meeting)
        # send message
        start_thread(self._send_message, (meeting, self.update_message_adapter_impl))
        logger.info('[MeetingApp/update] {}/{}: update meeting which mid is {} and id is {}.'
                    .format(meeting["community"], meeting["platform"], meeting["mid"], meeting["id"]))
        return result

    def delete(self, request, meeting_id):
        """delete meeting"""
        meeting = self.meeting_dao.get_by_id(meeting_id)
        if not meeting:
            logger.error('[MeetingApp/delete]Invalid meeting id:{}'.format(meeting_id))
            raise MyValidationError(RetCode.INFORMATION_CHANGE_ERROR)
        meeting = model_to_dict(meeting)
        set_log_thread_local(request, log_key, [meeting["community"], meeting["topic"], meeting_id])
        meeting.update({"sequence": meeting["sequence"] + 1})
        # check not delete in the before in start date
        self._is_in_prepare_meeting_duration_before_meeting(meeting)
        # delete meeting
        self.meeting_adapter_impl.delete(meeting)
        # update is_delete=1 in database
        result = self._delete_dao(meeting_id)
        # send message
        start_thread(self._send_message, (meeting, self.delete_message_adapter_impl))
        logger.info('[MeetingApp/delete] {}/{}: delete meeting which mid is {} and id is {}.'
                    .format(meeting["community"], meeting["platform"], meeting["mid"], meeting_id))
        return result

    def get_participants(self, meeting_id):
        """get participants"""
        meeting = self.meeting_dao.get_by_id(meeting_id)
        if not meeting:
            logger.error('[MeetingApp/get_participants]Invalid meeting id:{}'.format(meeting_id))
            raise MyValidationError(RetCode.INFORMATION_CHANGE_ERROR)
        meeting_participants = self.meeting_participants_dao.get(meeting_id)
        if meeting_participants:
            return meeting_participants.participants.split(",")
        return list()

    @staticmethod
    def get_meeting_platform(community):
        """get platform"""
        if community not in settings.COMMUNITY_HOST.keys():
            raise MyValidationError(RetCode.STATUS_PARAMETER_ERROR)
        host_info = settings.COMMUNITY_HOST.get(community)
        if host_info is not None:
            return list(host_info.keys())
        return list()

    def get_meeting_date(self, community, group_name, date):
        queryset = self.meeting_dao.get_queryset().filter(is_delete=0)
        if community is not None:
            queryset = queryset.filter(community=community)
        if group_name is not None:
            queryset = queryset.filter(group_name=group_name)
        if date is None:
            date = datetime.datetime.now()
        else:
            date = datetime.datetime.strptime(date, "%Y-%m-%d")
        start_date = (date - datetime.timedelta(days=31)).strftime('%Y-%m-%d')
        end_date = (date + datetime.timedelta(days=31)).strftime('%Y-%m-%d')
        queryset = queryset.filter(date__gte=start_date, date__lte=end_date)
        queryset_data = queryset.distinct().order_by('-date', 'id').values_list("date", flat=True)
        return [date for date in queryset_data]

    @staticmethod
    def get_time_range_meeting(queryset, time_range):
        time_range_domain = TimeRange.check_value(time_range)
        cur_date = datetime.datetime.now()
        queryset_data = {
            TimeRange.WEEKLY.value: queryset.filter((Q(date__gte=str(cur_date - datetime.timedelta(days=7))[:10]) &
                                                     Q(date__lte=str(cur_date + datetime.timedelta(days=7))[:10]))),
            TimeRange.RECENTLY.value: queryset.filter(date__gte=cur_date.strftime('%Y-%m-%d')),
            TimeRange.DAILY.value: queryset.filter(date=str(cur_date)[:10]),
            TimeRange.AFTER_WEEKLY.value: queryset.filter((Q(date__gte=cur_date.strftime('%Y-%m-%d')) &
                                                           Q(date__lte=str(cur_date + datetime.timedelta(days=7))[:10]))
                                                          ),
        }
        return queryset_data.get(time_range_domain.value)
