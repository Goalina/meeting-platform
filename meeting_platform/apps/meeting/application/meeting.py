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
import calendar

from django.conf import settings
from django.utils import timezone
from django.forms import model_to_dict
from django.db.models import Q
from django.db import transaction

from meeting.domain.primitive.upload_status import UploadStatus
from meeting.domain.primitive.time_range import TimeRange
from meeting.domain.primitive.cycle_type import CycleType
from meeting_platform.utils.common import start_thread, get_cur_date
from meeting_platform.utils.operation_log import set_log_thread_local, log_key
from meeting_platform.utils.ret_api import MyValidationError
from meeting_platform.utils.ret_code import RetCode
from meeting.infrastructure.adapter.meeting_adapter_impl.meeting_adapter_impl import MeetingAdapterImpl
from meeting.infrastructure.dao import meeting_dao, meeting_participants_dao
from meeting.infrastructure.adapter.message_adapter_impl.email_adapter_impl import CreateMessageEmailAdapterImpl, \
    DeleteMessageEmailAdapterImpl, UpdateMessageEmailAdapterImpl
from meeting.infrastructure.adapter.message_adapter_impl.kafka_adapter_impl import CreateMessageKafKaAdapterImpl, \
    DeleteMessageKafKaAdapterImpl, UpdateMessageKafKaAdapterImpl
from meeting.infrastructure.dao.meeting_records_obs_dao import MeetingRecordsObsDao
from meeting.infrastructure.dao.meeting_records_bili_dao import MeetingRecordsBiliDao
from meeting.infrastructure.dao.meeting_cycle_dao import MeetingCycleDao
from meeting.infrastructure.dao.meeting_cycle_sub_dao import MeetingCycleSubMeetingDao

logger = logging.getLogger("log")


class MeetingApp:
    meeting_dao = meeting_dao.MeetingDao
    meeting_cycle_dao = MeetingCycleDao
    meeting_cycle_sub_dao = MeetingCycleSubMeetingDao
    meeting_obs_records_dao = MeetingRecordsObsDao
    meeting_bili_records_dao = MeetingRecordsBiliDao
    meeting_participants_dao = meeting_participants_dao.MeetingParticipantsDao
    meeting_adapter_impl = MeetingAdapterImpl()
    create_message_adapter_impl = [CreateMessageEmailAdapterImpl, CreateMessageKafKaAdapterImpl]
    update_message_adapter_impl = [UpdateMessageEmailAdapterImpl, UpdateMessageKafKaAdapterImpl]
    delete_message_adapter_impl = [DeleteMessageEmailAdapterImpl, DeleteMessageKafKaAdapterImpl]

    @staticmethod
    def _get_cycle_date_by_policy(meeting):
        """get the cycle date by policy"""
        meeting_date_list = list()
        start_date = datetime.datetime.strptime(meeting["cycle_start_date"], "%Y-%m-%d")
        end_date = datetime.datetime.strptime(meeting["cycle_end_date"], "%Y-%m-%d")
        if meeting["cycle_type"] == CycleType.DAY:
            while start_date <= end_date:
                start_date += datetime.timedelta(days=meeting["cycle_interval"])
                meeting_date_list.append(
                    {
                        "date": start_date,
                        "start": meeting["cycle_start"],
                        "end": meeting["cycle_end"]
                    }
                )
        elif meeting["cycle_type"] == CycleType.Week:
            for wd in meeting["cycle_point"]:
                current = start_date + datetime.timedelta(days=(wd - (start_date.weekday() + 1) + 7) % 7)
                while current <= end_date:
                    meeting_date_list.append(
                        {
                            "date": current,
                            "start": meeting["cycle_start"],
                            "end": meeting["cycle_end"]
                        }
                    )
                    current += datetime.timedelta(weeks=1)
        elif meeting["cycle_type"] == CycleType.Month:
            # 从月份第一天开始
            current_month = start_date.replace(day=1)
            while current_month <= end_date:
                year, month = current_month.year, current_month.month
                # 获取当月最后一天
                last_day = calendar.monthrange(year, month)[1]
                for day in meeting["cycle_point"]:
                    # 处理无效日期
                    meeting_day = min(day, last_day)
                    meeting_date = datetime.datetime(year, month, meeting_day)
                    # 如果早于start_time，跳过
                    if meeting_date < start_date:
                        continue
                    if meeting_date <= end_date:
                        meeting_date_list.append(
                            {
                                "date": meeting_date,
                                "start": meeting["cycle_start"],
                                "end": meeting["cycle_end"]
                            }
                        )
                if month == 12:
                    current_month = datetime.datetime(year + 1, 1, 1)
                else:
                    current_month = datetime.datetime(year, month + 1, 1)
            else:
                logger.info("invalid cycle type")
        return meeting_date_list

    def _get_and_check_conflict_meetings_by_date(self, meeting, meeting_id=None):
        """check the conflict the meeting, if not conflict and return meeting"""
        unavailable_host_ids = list()
        community = meeting["community"]
        platform = meeting["platform"]
        if not meeting["is_cycle"]:
            date = meeting["date"]
            start = meeting["start"]
            end = meeting["end"]
            start_search = datetime.datetime.strftime(
                (datetime.datetime.strptime(start, '%H:%M') - datetime.timedelta(minutes=30)),
                '%H:%M')
            end_search = datetime.datetime.strftime(
                (datetime.datetime.strptime(end, '%H:%M') + datetime.timedelta(minutes=30)),
                '%H:%M')
            # get the normal unavailable host
            unavailable_host_ids = self.meeting_dao.get_conflict_meeting(community, platform, date,
                                                                         start_search, end_search, meeting_id)
        else:
            cycle_dates = self._get_cycle_date_by_policy(meeting)
            for cycle_date in cycle_dates:
                start_search = datetime.datetime.strftime(
                    (datetime.datetime.strptime(cycle_date["start"], '%H:%M') - datetime.timedelta(minutes=30)),
                    '%H:%M')
                end_search = datetime.datetime.strftime(
                    (datetime.datetime.strptime(cycle_date["end"], '%H:%M') + datetime.timedelta(minutes=30)),
                    '%H:%M')
                # 会议的mid
                unavailable_host_ids = self.meeting_dao.get_conflict_meeting(community, platform, cycle_date["date"],
                                                                             start_search, end_search, meeting_id)
        # get the all host
        host_info = settings.COMMUNITY_HOST[meeting["community"]][meeting["platform"]]
        host_list = [key["HOST"] for key in host_info]
        available_host_id = list(set(host_list) - set(unavailable_host_ids))
        if len(available_host_id) == 0:
            logger.info('[MeetingApp/_get_and_check_conflict_meetings_by_date] '
                        '{}/{}: no available host'.format(meeting["community"], meeting["platform"]))
            raise MyValidationError(RetCode.STATUS_MEETING_DATE_CONFLICT)
        return available_host_id

    @staticmethod
    def _is_in_prepare_meeting_duration_before_meeting(meeting, start_date_str=None):
        if not meeting["is_cycle"]:
            if start_date_str is None:
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
        """calc the meeting count"""
        today = timezone.now().date()
        meeting_counts = self.meeting_dao.get_today_meeting_counts(meeting["community"], meeting["sponsor"], today)
        if meeting_counts >= settings.MEETING_CREATE_COUNT:
            raise MyValidationError(RetCode.STATUS_MEETING_CREATE_COUNT_LIMIT)

    def _check_recurring_meetings(self, meeting):
        """check recurring meeting"""
        if not meeting["is_cycle"]:
            m_count = self.meeting_dao.get_repeat_meeting_by_community_sponsor_date_start_counts(meeting["community"],
                                                                                                 meeting["group_name"],
                                                                                                 meeting["sponsor"],
                                                                                                 meeting["date"],
                                                                                                 meeting["start"])
        else:
            mid = self.meeting_dao.get_repeat_meeting_by_cycle_mid(meeting["community"],
                                                                   meeting["group_name"],
                                                                   meeting["sponsor"])
            m_count = self.meeting_cycle_dao.get_by_mid_and_info(mid,
                                                                 meeting["cycle_start_date"],
                                                                 meeting["cycle_end_date"],
                                                                 meeting["cycle_start"],
                                                                 meeting["cycle_end"],
                                                                 meeting["cycle_type"].value)
        if m_count != 0:
            raise MyValidationError(RetCode.STATUS_MEETING_REPEAT_FAILED)

    def _save_dao(self, meeting):
        with transaction.atomic():
            if meeting["is_record"]:
                obs_record_obj = self.meeting_obs_records_dao.create(UploadStatus.INIT.value, meeting["mid"])
                meeting["obs_records"] = obs_record_obj
                bili_record_obj = self.meeting_bili_records_dao.create(UploadStatus.INIT.value, meeting["mid"])
                meeting["bili_records"] = bili_record_obj
            else:
                meeting["obs_records"] = None
                meeting["bili_records"] = None
            meeting_data = {
                "sponsor": meeting.get("sponsor"),
                "group_name": meeting.get("group_name"),
                "community": meeting.get("community"),
                "topic": meeting.get("topic"),
                "platform": meeting.get("platform"),
                "is_cycle": meeting.get("is_cycle"),
                "date": meeting.get("date"),
                "start": meeting.get("start"),
                "end": meeting.get("end"),
                "agenda": meeting.get("agenda"),
                "etherpad": meeting.get("etherpad"),
                "email_list": meeting.get("email_list"),
                "host_id": meeting.get("host_id"),
                "mid": meeting.get("mid"),
                "m_mid": meeting.get("m_mid"),
                "join_url": meeting.get("join_url"),
                "is_record": meeting.get("is_record"),
                "obs_records": meeting.get("obs_records"),
                "bili_records": meeting.get("bili_records"),
            }
            meeting_obj = self.meeting_dao.create(**meeting_data)
            if meeting["is_cycle"]:
                for sub_meeting in meeting.get("sub_info"):
                    cycle_sub_meeting = {
                        "mid": meeting["mid"],
                        "sub_id": sub_meeting["sub_id"],
                        "date": sub_meeting["date"],
                        "start": sub_meeting["start"],
                        "end": sub_meeting["end"],
                        "meeting": meeting_obj,
                    }
                    self.meeting_cycle_sub_dao.create(**cycle_sub_meeting)
                cycle_date = {
                    "mid": meeting["mid"],
                    "start_date": meeting.get("cycle_start_date"),
                    "end_date": meeting.get("cycle_end_date"),
                    "start": meeting.get("cycle_start"),
                    "end": meeting.get("cycle_end"),
                    "cycle_type": meeting.get("cycle_type").value,
                    "interval": meeting.get("cycle_interval"),
                    "meeting": meeting_obj,
                    "point": ",".join([str(i) for i in meeting["cycle_point"]])
                    if meeting.get("cycle_point") is not None else None,
                }
                self.meeting_cycle_dao.create(**cycle_date)
            return meeting_obj.id

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
                meeting["bili_records"] = bili_record_obj
            else:
                if obs_record_obj:
                    self.meeting_dao.update_obs_records_by_mid(meeting["mid"])
                    self.meeting_obs_records_dao.delete_by_mid(meeting["mid"])
                    meeting["obs_records"] = None
                if bili_record_obj:
                    self.meeting_dao.update_bili_records_by_mid(meeting["mid"])
                    self.meeting_bili_records_dao.delete_by_mid(meeting["mid"])
                    meeting["bili_records"] = None
            if meeting["is_cycle"]:
                meeting_obj = self.meeting_dao.get_by_mid(meeting["mid"])
                sub_info = meeting.pop("sub_info")
                self.meeting_cycle_sub_dao.delete_by_mid(meeting["mid"])
                for sub_meeting in sub_info:
                    self.meeting_cycle_sub_dao.create(
                        mid=meeting["mid"],
                        sub_id=sub_meeting["sub_id"],
                        date=sub_meeting["date"],
                        start=sub_meeting["start"],
                        end=sub_meeting["end"],
                        meeting=meeting_obj,
                    )
                cycle_date = {
                    "mid": meeting["mid"],
                    "start_date": meeting.get("cycle_start_date"),
                    "end_date": meeting.get("cycle_end_date"),
                    "start": meeting.get("cycle_start"),
                    "end": meeting.get("cycle_end"),
                    "cycle_type": meeting["cycle_type"].value,
                    "interval": meeting.get("cycle_interval"),
                    "meeting": meeting_obj,
                    "point": ",".join([str(i) for i in meeting["cycle_point"]])
                    if meeting.get("cycle_point") is not None else None,
                }
                if self.meeting_cycle_dao.get_by_id(meeting["mid"]) is not None:
                    meeting["cycle_date"] = self.meeting_cycle_dao.create(**cycle_date)
                else:
                    del cycle_date["mid"]
                    self.meeting_cycle_dao.update(meeting["mid"], **cycle_date)
            else:
                meeting["cycle_date"] = None
            logger.info(meeting)
            return self.meeting_dao.update_by_id(meeting_id,
                                                 topic=meeting["topic"],
                                                 agenda=meeting["agenda"],
                                                 is_record=meeting["is_record"],
                                                 is_cycle=meeting["is_cycle"],
                                                 date=meeting["date"],
                                                 start=meeting["start"],
                                                 end=meeting["end"],
                                                 obs_records=meeting["obs_records"],
                                                 bili_records=meeting["bili_records"],
                                                 )

    def _update_sub_dao(self, meeting):
        with transaction.atomic():
            self.meeting_cycle_sub_dao.update_by_mid_and_sub_id(meeting["mid"],
                                                                meeting["sub_id"],
                                                                date=meeting["date"],
                                                                start=meeting["start"],
                                                                end=meeting["end"])
            return self.meeting_dao.update_by_id(meeting["id"], is_record=meeting["is_record"])

    def _delete_dao(self, meeting_id, meeting):
        with transaction.atomic():
            meeting_obj = self.meeting_dao.get_by_id(meeting_id)
            self.meeting_dao.delete_by_id(meeting_id)
            self.meeting_bili_records_dao.delete_by_mid(meeting_obj.mid)
            self.meeting_obs_records_dao.delete_by_mid(meeting_obj.mid)
            # self.meeting_cycle_dao.delete_by_mid(meeting["mid"])
            self.meeting_cycle_sub_dao.delete_by_mid(meeting["mid"])
        return meeting_id

    def _delete_sub_dao(self, mid, sub_id):
        return self.meeting_cycle_sub_dao.delete_by_mid_and_sub_id(mid, sub_id)

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
        meeting_info = self.meeting_adapter_impl.create(meeting["host_id"], meeting)
        meeting.update(meeting_info)
        # create in database
        result_id = self._save_dao(meeting)
        meeting["id"] = result_id
        # send message
        start_thread(self._send_message, (meeting, self.create_message_adapter_impl))
        logger.info('[MeetingApp/create] {}/{}: create meeting which mid is {} and id is {}.'.
                    format(meeting["community"], meeting["platform"], meeting["mid"], result_id))
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
        resp = self.meeting_adapter_impl.update(meeting)
        meeting.update(resp)
        # update in database
        result = self._update_dao(meeting_id, meeting)
        # send message
        start_thread(self._send_message, (meeting, self.update_message_adapter_impl))
        logger.info('[MeetingApp/update] {}/{}: update meeting which mid is {} and id is {}.'
                    .format(meeting["community"], meeting["platform"], meeting["mid"], meeting["id"]))
        return result

    def update_sub(self, meeting_data):
        meeting = self.meeting_dao.get_by_mid(meeting_data["mid"])
        if not meeting:
            logger.error('[MeetingApp/update_sub]Invalid meeting mid:{}'.format(meeting_data["mid"]))
            raise MyValidationError(RetCode.INFORMATION_CHANGE_ERROR)
        meeting_sub_info = self.meeting_cycle_sub_dao.get_by_mid_and_sub_id(meeting_data["mid"], meeting_data["sub_id"])
        if not meeting_sub_info:
            logger.error('[MeetingApp/update_sub]Invalid meeting mid:{}/{}'.format(meeting_data["mid"],
                                                                                   meeting_data["sub_id"]))
            raise MyValidationError(RetCode.INFORMATION_CHANGE_ERROR)
        meeting = model_to_dict(meeting)
        meeting.update({"sequence": meeting["sequence"] + 1})
        meeting.update(meeting_data)
        # check modify meeting count
        if meeting["sequence"] > settings.MEETING_MODIFY_COUNT + 1:
            raise MyValidationError(RetCode.STATUS_MEETING_MODIFY_COUNT_LIMIT)
        # check meeting-conflict
        # self._get_and_check_conflict_meetings_by_date(meeting, meeting["id"])
        # check not update in the before in start date
        self._is_in_prepare_meeting_duration_before_meeting(meeting)
        # update meeting
        self.meeting_adapter_impl.update_sub(meeting)
        # update in database
        result = self._update_sub_dao(meeting)
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
        result = self._delete_dao(meeting_id, meeting)
        # send message
        start_thread(self._send_message, (meeting, self.delete_message_adapter_impl))
        logger.info('[MeetingApp/delete] {}/{}: delete meeting which mid is {} and id is {}.'
                    .format(meeting["community"], meeting["platform"], meeting["mid"], meeting_id))
        return result

    def delete_sub(self, sub_id):
        """delete sub meeting"""
        sub_info = self.meeting_cycle_sub_dao.get_by_sub_id(sub_id)
        if sub_info is None:
            logger.error('[MeetingApp/delete_sub]Invalid meeting sub id:{}'.format(sub_id))
            raise MyValidationError(RetCode.INFORMATION_CHANGE_ERROR)
        mid = sub_info.mid
        meeting = self.meeting_dao.get_by_mid(mid)
        if not meeting:
            logger.error('[MeetingApp/delete_sub]Invalid meeting id:{}'.format(meeting["id"]))
            raise MyValidationError(RetCode.INFORMATION_CHANGE_ERROR)
        meeting_sub_info = self.meeting_cycle_sub_dao.get_by_mid_and_sub_id(mid, sub_id)
        if not meeting_sub_info:
            logger.error('[MeetingApp/delete_sub]Invalid meeting id:{}/{}'.format(mid, sub_id))
            raise MyValidationError(RetCode.INFORMATION_CHANGE_ERROR)
        meeting = model_to_dict(meeting)
        meeting.update({"sequence": meeting["sequence"] + 1})
        meeting.update(model_to_dict(sub_info))
        logger.info(meeting)
        # check not delete in the before in start date
        start_date_str = "{} {}".format(meeting_sub_info.date, meeting_sub_info.start)
        self._is_in_prepare_meeting_duration_before_meeting(meeting, start_date_str)
        # delete meeting
        self.meeting_adapter_impl.delete_sub(meeting)
        # update is_delete=1 in database
        result = self._delete_sub_dao(mid, sub_id)
        # send message
        start_thread(self._send_message, (meeting, self.delete_message_adapter_impl))
        logger.info('[MeetingApp/delete_sub] {}/{}: delete meeting which mid is {} and id is {}.'
                    .format(meeting["community"], meeting["platform"], meeting["mid"], meeting["id"]))
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
        # 处理非周期性会议
        start_date = (date - datetime.timedelta(days=31)).strftime('%Y-%m-%d')
        end_date = (date + datetime.timedelta(days=31)).strftime('%Y-%m-%d')
        queryset_data = queryset.filter(date__gte=start_date, date__lte=end_date). \
            distinct().order_by('-date', 'id').values_list("date", flat=True)
        normal_data = set(date for date in queryset_data)
        # 处理周期性会议, 算出一个月的mid
        cycle_all_mid = self.meeting_cycle_sub_dao.get_all(). \
            filter(date__gte=start_date, date__lte=end_date).values_list("mid", flat=True)
        cycle_mid = queryset.filter(mid__in=cycle_all_mid).values_list("mid", flat=True)
        cycle_queryset_data = self.meeting_cycle_sub_dao.get_all().filter(mid__in=cycle_mid).distinct(). \
            order_by('-date', 'id').values_list("date", flat=True)
        cycle_data = set(date for date in cycle_queryset_data)
        all_date = sorted(list(normal_data.union(cycle_data)))
        return list(all_date)

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
