#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/6/20 20:20
# @Author  : Tom_zc
# @FileName: test_meetings.py
# @Software: PyCharm
import copy
import datetime
import logging
import secrets
import time
from unittest import mock
from datetime import timedelta

from rest_framework import status
from django.conf import settings

from meeting.application.meeting import MeetingApp
from meeting_platform.test.meeting.constant import xss_script, html_text, crlf_text
from meeting_platform.test.meeting.test_base import TestCommonMeeting
from meeting_platform.utils.ret_api import MyInnerError
from meeting_platform.utils.ret_code import RetCode

logger = logging.getLogger("log")

_invalid_params = [xss_script, html_text, crlf_text, ""]


# noinspection SpellCheckingInspection
class CreateMeetingViewTest(TestCommonMeeting):
    url = "/inner/v1/meeting/meeting/"
    data = {
        "sponsor": "Tom",  # string类型，会议发起人，必填，长度限制64，限制内容中含有http，\r\n，xss攻击标签
        "group_name": "group_temp",  # string类型，sig组名称，必填，长度限制64，限制内容中含有http，\r\n，xss攻击标签
        "community": "openEuler",  # string类型，community字段必须与配置中COMMUNITY_SUPPORT字段保持一致
        "topic": "meeting unitest create topic",  # string类型，会议名称，必填，长度限制128，限制内容中含有http，\r\n，xss攻击标签
        "platform": "WELINK",  # string类型，平台，只能是以下参数: ZOOM,WELINK,TENCENT，必填
        "date": str(datetime.datetime.now().date() + timedelta(days=1)),  # string类型，时间：2023-10-29，必填
        "start": "08:00",  # string类型，开始时间，必填
        "end": "09:00",  # string类型，结束时间，必填

        # string类型，文本纪要链接，必填，内容可为空，限制255
        "etherpad": "https://xxx.com/p/infrastructure",

        "agenda": "今天开个会议",  # string类型，开会内容，必填，内容可以为空， 限制为4096，限制内容中含有http，\r\n, xss攻击标签
        "email_list": "",  # string类型, 发送邮件，以;拼接，长度最长为1000，每封邮箱长度最长为50，限制20封，必填，内容可以为空
        "is_record": True  # bool类型，是否自动录制，必填，true为自动录制，false代表自动关闭录制
    }

    def _setup(self):
        user = self.create_user()
        self.enable_client_auth(user.username)
        return user

    def _teardown(self):
        meeting = self.get_meetings()
        logger.info("find meeting:{}".format(len(meeting)))
        for meeting in meeting:
            uri = DeleteMeetingViewTest.url.format(meeting.id)
            self.client.delete(uri)
        self.clear_user()

    def get_invalid_params(self, data=None):
        fields = copy.deepcopy(_invalid_params)
        if data is not None:
            fields.append(data)
        return fields

    def test_params_sponsor_failed(self):
        self._setup()
        data = copy.deepcopy(self.data)
        fields = self.get_invalid_params("*" * 65)
        for params in fields:
            data["sponsor"] = params
            ret = self.client.post(self.url, data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown()

    def test_params_topic_failed(self):
        self._setup()
        data = copy.deepcopy(self.data)
        fields = self.get_invalid_params("*" * 129)
        for params in fields:
            data["topic"] = params
            ret = self.client.post(self.url, data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown()

    def test_params_platform_failed(self):
        self._setup()
        data = copy.deepcopy(self.data)
        fields = self.get_invalid_params("*" * 129)
        for params in fields:
            data["platform"] = params
            ret = self.client.post(self.url, data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown()

    def test_params_community_failed(self):
        self._setup()
        data = copy.deepcopy(self.data)
        fields = self.get_invalid_params("*" * 129)
        for params in fields:
            data["community"] = params
            ret = self.client.post(self.url, data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown()

    def test_params_group_name_failed(self):
        self._setup()
        data = copy.deepcopy(self.data)
        fields = self.get_invalid_params("*" * 65)
        for params in fields:
            data["group_name"] = params
            ret = self.client.post(self.url, data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown()

    def test_params_etherpad_failed(self):
        self._setup()
        data = copy.deepcopy(self.data)
        fields = self.get_invalid_params()
        for params in fields:
            if not params or params == crlf_text:
                continue
            data["etherpad"] = params
            ret = self.client.post(self.url, data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown()

    # noinspection SpellCheckingInspection
    def test_params_email_list_failed(self):
        self._setup()
        data = copy.deepcopy(self.data)
        fields = self.get_invalid_params()
        fields.extend([
            "abcdefghjklmnopqrstuvwxyz;asd@qq.com",
            ";".join(["{}@163.com".format("a" * 42) for _ in range(51)]),
            ";".join(["{}163.com".format("a" * 42) for _ in range(10)]),
        ])
        for params in fields:
            if not params or params == crlf_text:
                continue
            data["email_list"] = params
            ret = self.client.post(self.url, data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown()

    def test_params_agenda_failed(self):
        self._setup()
        data = copy.deepcopy(self.data)
        fields = self.get_invalid_params()
        fields.append("*" * 4097)
        for params in fields:
            if not params or params == crlf_text:
                continue
            data["agenda"] = params
            ret = self.client.post(self.url, data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown()

    def test_params_is_record_failed(self):
        self._setup()
        data = copy.deepcopy(self.data)
        fields = self.get_invalid_params()
        for params in fields:
            data["is_record"] = params
            ret = self.client.post(self.url, data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown()

    def test_params_date_failed(self):
        self._setup()
        data = copy.deepcopy(self.data)
        fields = self.get_invalid_params(str(datetime.datetime.now().date() - timedelta(days=2)))
        for params in fields:
            data["date"] = params
            ret = self.client.post(self.url, data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown()

    def test_params_start_failed(self):
        self._setup()
        data = copy.deepcopy(self.data)
        fields = self.get_invalid_params("08:1x")
        for params in fields:
            data["start"] = params
            ret = self.client.post(self.url, data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        for params in ["07:15", "22:15", "15:10", "15:60", "15:-1"]:
            data["start"] = params
            ret = self.client.post(self.url, data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown()

    def test_params_end_failed(self):
        self._setup()
        data = copy.deepcopy(self.data)
        fields = self.get_invalid_params("08:1x")
        for params in fields:
            data["end"] = params
            ret = self.client.post(self.url, data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        for params in ["07:15", "23:15", "15:10", "15:60", "15:-1"]:
            data["end"] = params
            ret = self.client.post(self.url, data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown()

    def test_invalid_check_duration_failed(self):
        self._setup()
        data = copy.deepcopy(self.data)
        cur_date = datetime.datetime.now()
        start_date = cur_date - datetime.timedelta(days=2)
        end_date = cur_date - datetime.timedelta(days=2)
        data["start"] = "{}:15".format(start_date.hour)
        data["end"] = "{}:15".format(end_date.hour)
        ret = self.client.post(self.url, data=data)
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        start_date = cur_date + datetime.timedelta(days=61)
        data["date"] = str(start_date.date())
        ret = self.client.post(self.url, data=data)
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        data["date"] = str(datetime.datetime.now().date())
        start_date = cur_date + datetime.timedelta(hours=2)
        end_date = cur_date + datetime.timedelta(hours=3)
        data["start"] = "{}:15".format(end_date.hour)
        data["end"] = "{}:15".format(start_date.hour)
        ret = self.client.post(self.url, data=data)
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown()

    def test_conflict_meeting_failed(self):
        self._setup()
        data = copy.deepcopy(self.data)
        platform = settings.COMMUNITY_HOST[data["community"]][data["platform"]]
        for i in range(len(platform)):
            self.client.post(self.url, data)
        ret = self.client.post(self.url, data)
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown()

    @mock.patch("meeting.infrastructure.adapter.meeting_adapter_impl.meeting_adapter_impl.MeetingAdapterImpl.create")
    def test_create_meeting_failed(self, mock_create):
        self._setup()
        data = copy.deepcopy(self.data)
        mock_create.side_effect = MyInnerError(RetCode.STATUS_MEETING_FAILED_CREATE)
        ret = self.client.post(self.url, data)
        self.assertEqual(ret.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self._teardown()

    def test_create_meeting_ok_by_welink_and_record(self):
        self._setup()
        data = copy.deepcopy(self.data)
        ret = self.client.post(self.url, data)
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        self._teardown()

    def test_create_meeting_ok_by_zoom_and_record(self):
        self._setup()
        data = copy.deepcopy(self.data)
        data["platform"] = "ZOOM"
        ret = self.client.post(self.url, data)
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        self._teardown()

    def test_create_meeting_ok_by_tecent_and_record(self):
        self._setup()
        data = copy.deepcopy(self.data)
        data["platform"] = "TENCENT"
        ret = self.client.post(self.url, data)
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        self._teardown()

    def test_create_meeting_ok_by_welink_and_not_record(self):
        self._setup()
        data = copy.deepcopy(self.data)
        data["sponsor"] = "a" * 64
        data["group_name"] = "b" * 64
        data["topic"] = "c" * 128
        data["agenda"] = "c" * 4096
        data["is_record"] = False
        ret = self.client.post(self.url, data)
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        self._teardown()

    def test_create_meeting_ok_by_zoom_and_not_record(self):
        self._setup()
        data = copy.deepcopy(self.data)
        data["sponsor"] = "a" * 64
        data["group_name"] = "b" * 64
        data["topic"] = "c" * 128
        data["agenda"] = "c" * 4096
        data["platform"] = "ZOOM"
        data["is_record"] = False
        ret = self.client.post(self.url, data)
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        self._teardown()

    def test_create_meeting_ok_by_tecent_and_not_record(self):
        self._setup()
        data = copy.deepcopy(self.data)
        data["sponsor"] = "a" * 64
        data["group_name"] = "b" * 64
        data["topic"] = "c" * 128
        data["agenda"] = "c" * 4096
        data["platform"] = "TENCENT"
        data["is_record"] = False
        ret = self.client.post(self.url, data)
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        self._teardown()


class UpdateMeetingViewTest(TestCommonMeeting):
    url = "/inner/v1/meeting/meeting/{}/"
    data = {
        "topic": "meeting unitest update topic",  # string类型，会议名称，必填，长度限制128，限制内容中含有http，\r\n，xss攻击标签
        "date": str(datetime.datetime.now().date() + timedelta(days=1)),  # string类型，时间：2023-10-29，必填
        "start": "10:00",  # string类型，开始时间，必填
        "end": "11:00",  # string类型，结束时间，必填
        # string类型，文本纪要链接，必填，内容可为空，限制255
        "etherpad": "https://xxxx.com/p/infrastructure",
        "agenda": "今天开个会议",  # string类型，开会内容，必填，内容可以为空， 限制为4096，限制内容中含有http，\r\n, xss攻击标签
        "is_record": False  # bool类型，是否自动录制，必填，true为自动录制，false代表自动关闭录制
    }

    def _setup(self):
        user = self.create_user()
        self.enable_client_auth(user.username)
        return user

    def _create_meeting(self, username, is_create_meeting=False):
        if is_create_meeting:
            data = copy.deepcopy(CreateMeetingViewTest.data)
            data["sponsor"] = username
            self.client.post(CreateMeetingViewTest.url, data)
            return self.get_meeting_by_username(username)
        data = copy.deepcopy(CreateMeetingViewTest.data)
        available_host_id = MeetingApp()._get_and_check_conflict_meetings_by_date(data)
        data["host_id"] = secrets.choice(available_host_id)
        data["sponsor"] = username
        return self.create_meeting(**data)

    def _teardown(self):
        meeting = self.get_meetings()
        logger.info("find meeting:{}".format(len(meeting)))
        for meeting in meeting:
            uri = DeleteMeetingViewTest.url.format(meeting.id)
            self.client.delete(uri)
        self.clear_user()

    def get_invalid_params(self, data=None):
        fields = copy.deepcopy(_invalid_params)
        if data is not None:
            fields.append(data)
        return fields

    def test_params_topic_failed(self):
        self._setup()
        data = copy.deepcopy(self.data)
        fields = self.get_invalid_params("*" * 129)
        for params in fields:
            data["topic"] = params
            ret = self.client.put(self.url.format(1), data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown()

    def test_params_agenda_failed(self):
        self._setup()
        data = copy.deepcopy(self.data)
        fields = self.get_invalid_params()
        for params in fields:
            if not params or params == crlf_text:
                continue
            data["agenda"] = params
            ret = self.client.put(self.url.format(1), data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown()

    def test_params_is_record_failed(self):
        self._setup()
        data = copy.deepcopy(self.data)
        fields = self.get_invalid_params()
        for params in fields:
            data["is_record"] = params
            ret = self.client.put(self.url.format(1), data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown()

    def test_params_date_failed(self):
        self._setup()
        data = copy.deepcopy(self.data)
        fields = self.get_invalid_params(str(datetime.datetime.now().date() - timedelta(days=1)))
        for params in fields:
            data["date"] = params
            ret = self.client.put(self.url.format(1), data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown()

    def test_params_start_failed(self):
        self._setup()
        data = copy.deepcopy(self.data)
        fields = self.get_invalid_params("08:1x")
        for params in fields:
            data["start"] = params
            ret = self.client.put(self.url.format(1), data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        for params in ["07:15", "22:15", "15:10", "15:60", "15:-1"]:
            data["start"] = params
            ret = self.client.put(self.url.format(1), data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown()

    def test_params_end_failed(self):
        self._setup()
        data = copy.deepcopy(self.data)
        fields = self.get_invalid_params("08:1x")
        for params in fields:
            data["end"] = params
            ret = self.client.put(self.url.format(1), data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        for params in ["07:15", "23:15", "15:10", "15:60", "15:-1"]:
            data["end"] = params
            ret = self.client.put(self.url.format(1), data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown()

    def test_params_etherpad_failed(self):
        self._setup()
        data = copy.deepcopy(self.data)
        fields = self.get_invalid_params()
        for params in fields:
            if not params or params == crlf_text:
                continue
            data["etherpad"] = params
            ret = self.client.put(self.url.format(1), data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown()

    def test_invalid_check_duration_failed(self):
        self._setup()
        data = copy.deepcopy(self.data)
        cur_date = datetime.datetime.now()
        start_date = cur_date - datetime.timedelta(days=2)
        end_date = cur_date + datetime.timedelta(days=2)
        data["start"] = "{}:15".format(start_date.hour)
        data["end"] = "{}:15".format(end_date.hour)
        ret = self.client.put(self.url.format(1), data=self.data)
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        start_date = cur_date + datetime.timedelta(days=61)
        data["date"] = str(start_date.date())
        data["start"] = "10:15"
        data["end"] = "12:15"
        ret = self.client.put(self.url.format(1), data=self.data)
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        data["date"] = str(datetime.datetime.now().date())
        start_date = cur_date + datetime.timedelta(hours=2)
        end_date = cur_date + datetime.timedelta(hours=3)
        data["start"] = "{}:15".format(end_date.hour)
        data["end"] = "{}:15".format(start_date.hour)
        ret = self.client.put(self.url.format(1), data=self.data)
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown()

    def test_conflict_meeting_failed(self):
        username = "anonymous"
        self._setup()
        # ready the one meeting
        platform = settings.COMMUNITY_HOST[CreateMeetingViewTest.data["community"]][
            CreateMeetingViewTest.data["platform"]]
        for i in range(len(platform)):
            self._create_meeting(username)
        # ready the two meeting
        data = copy.deepcopy(CreateMeetingViewTest.data)
        data["date"] = str(datetime.datetime.now().date() + timedelta(days=2))
        available_host_id = MeetingApp()._get_and_check_conflict_meetings_by_date(data)
        data["host_id"] = secrets.choice(available_host_id)
        data["sponsor"] = username
        meeting = self.create_meeting(**data)
        # put the two meeting
        update_data = copy.deepcopy(self.data)
        update_data["date"] = CreateMeetingViewTest.data["date"]
        update_data["start"] = CreateMeetingViewTest.data["start"]
        update_data["end"] = CreateMeetingViewTest.data["end"]
        ret = self.client.put(self.url.format(meeting.id), update_data)
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown()

    def test_cant_delete_in_before_one_hours(self):
        user = self._setup()
        data = copy.deepcopy(CreateMeetingViewTest.data)
        cur_date = datetime.datetime.now()
        data["sponsor"] = user.username
        data["date"] = cur_date.date()
        data["start"] = "{}:00".format(cur_date.hour + 1)
        data["end"] = "{}:00".format(cur_date.hour + 2)
        available_host_id = MeetingApp()._get_and_check_conflict_meetings_by_date(data)
        data["host_id"] = secrets.choice(available_host_id)
        meeting = self.create_meeting(**data)
        time.sleep(10)
        ret = self.client.put(self.url.format(meeting.id), data)
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown()

    @mock.patch("meeting.infrastructure.adapter.meeting_adapter_impl.meeting_adapter_impl.MeetingAdapterImpl.update")
    def test_update_meeting_failed(self, mock_update):
        user = self._setup()
        meeting = self._create_meeting(user.username)
        mock_update.side_effect = MyInnerError(RetCode.STATUS_MEETING_FAILED_UPDATE)
        ret = self.client.put(self.url.format(meeting.id), self.data)
        self._teardown()
        self.assertEqual(ret.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_update_meeting_ok_by_record(self):
        user = self._setup()
        data = copy.deepcopy(CreateMeetingViewTest.data)
        data["sponsor"] = user.username
        data["is_record"] = False
        self.client.post(CreateMeetingViewTest.url, data)
        meeting = self.get_meeting_by_username(user.username)
        data = copy.deepcopy(self.data)
        data["is_record"] = True
        ret = self.client.put(self.url.format(meeting.id), data)
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        self._teardown()

    def test_update_meeting_ok_by_not_record(self):
        user = self._setup()
        meeting = self._create_meeting(user.username, is_create_meeting=True)
        data = copy.deepcopy(self.data)
        ret = self.client.put(self.url.format(meeting.id), data)
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        self._teardown()


class DeleteMeetingViewTest(TestCommonMeeting):
    url = "/inner/v1/meeting/meeting/{}/"

    def _setup(self):
        user = self.create_user()
        self.enable_client_auth(user.username)
        return user

    def _teardown(self):
        meeting = self.get_meetings()
        logger.info("find meeting:{}".format(len(meeting)))
        for meeting in meeting:
            uri = DeleteMeetingViewTest.url.format(meeting.id)
            self.client.delete(uri)
        self.clear_user()

    def _create_meeting(self, username, is_create_meeting=False):
        if is_create_meeting:
            data = copy.deepcopy(CreateMeetingViewTest.data)
            data["sponsor"] = username
            self.client.post(CreateMeetingViewTest.url, data)
            return self.get_meeting_by_username(username)
        data = copy.deepcopy(CreateMeetingViewTest.data)
        available_host_id = MeetingApp()._get_and_check_conflict_meetings_by_date(data)
        data["host_id"] = secrets.choice(available_host_id)
        data["sponsor"] = username
        return self.create_meeting(**data)

    def test_cant_delete_in_before_one_hours(self):
        user = self._setup()
        data = copy.deepcopy(CreateMeetingViewTest.data)
        cur_date = datetime.datetime.now()
        data["sponsor"] = user.username
        data["date"] = cur_date.date()
        data["start"] = "{}:00".format(cur_date.hour + 1)
        data["end"] = "{}:00".format(cur_date.hour + 2)
        available_host_id = MeetingApp()._get_and_check_conflict_meetings_by_date(data)
        data["host_id"] = secrets.choice(available_host_id)
        meeting = self.create_meeting(**data)
        time.sleep(10)
        ret = self.client.delete(self.url.format(meeting.id))
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown()

    @mock.patch("meeting.infrastructure.adapter.meeting_adapter_impl.meeting_adapter_impl.MeetingAdapterImpl.delete")
    def test_delete_failed(self, mock_delete):
        user = self._setup()
        meeting = self._create_meeting(user.username)
        mock_delete.side_effect = MyInnerError(RetCode.STATUS_FAILED)
        ret = self.client.delete(self.url.format(meeting.id))
        self.assertEqual(ret.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self._teardown()

    def test_delete_ok(self):
        user = self._setup()
        meeting = self._create_meeting(user.username, is_create_meeting=True)
        ret = self.client.delete(self.url.format(meeting.id))
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        self._teardown()


class ListMeetingViewTest(TestCommonMeeting):
    url = "/inner/v1/meeting/meeting/"

    def _setup(self):
        user = self.create_user()
        self.enable_client_auth(user.username)
        return user

    def _teardown(self):
        meeting = self.get_meetings()
        logger.info("find meeting:{}".format(len(meeting)))
        for meeting in meeting:
            uri = DeleteMeetingViewTest.url.format(meeting.id)
            self.client.delete(uri)
        self.clear_user()

    def _create_meeting(self, username, is_create_meeting=False):
        if is_create_meeting:
            data = copy.deepcopy(CreateMeetingViewTest.data)
            data["sponsor"] = username
            data["platform"] = "TENCENT"
            self.client.post(CreateMeetingViewTest.url, data)
            return self.get_meeting_by_username(username)
        data = copy.deepcopy(CreateMeetingViewTest.data)
        available_host_id = MeetingApp()._get_and_check_conflict_meetings_by_date(data)
        data["host_id"] = secrets.choice(available_host_id)
        data["sponsor"] = username
        return self.create_meeting(**data)

    def test_list_ok(self):
        user = self._setup()
        self._create_meeting(user.username, is_create_meeting=True)
        ret = self.client.get(self.url)
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        self.assertEqual(ret.data["total"], 1)
        self.assertEqual(len(ret.data["data"]), 1)
        self._teardown()


class GetMeetingViewTest(TestCommonMeeting):
    url = "/inner/v1/meeting/meeting/{}/"

    def _setup(self):
        user = self.create_user()
        self.enable_client_auth(user.username)
        return user

    def _teardown(self):
        meeting = self.get_meetings()
        logger.info("find meeting:{}".format(len(meeting)))
        for meeting in meeting:
            uri = DeleteMeetingViewTest.url.format(meeting.id)
            self.client.delete(uri)
        self.clear_user()

    def _create_meeting(self, username, is_create_meeting=False):
        if is_create_meeting:
            data = copy.deepcopy(CreateMeetingViewTest.data)
            data["sponsor"] = username
            self.client.post(CreateMeetingViewTest.url, data)
            return self.get_meeting_by_username(username)
        data = copy.deepcopy(CreateMeetingViewTest.data)
        available_host_id = MeetingApp()._get_and_check_conflict_meetings_by_date(data)
        data["host_id"] = secrets.choice(available_host_id)
        data["sponsor"] = username
        return self.create_meeting(**data)

    def test_get_ok(self):
        user = self._setup()
        self._create_meeting(user.username)
        meeting = self.get_meeting_by_username(user.username)
        ret = self.client.get(self.url.format(meeting.id))
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        self._teardown()


class GetMeetingParticipantsViewTest(TestCommonMeeting):
    url = "/inner/v1/meeting/meeting/participants/{}/"

    def _setup(self):
        user = self.create_user()
        self.enable_client_auth(user.username)
        return user

    def _teardown(self):
        meeting = self.get_meetings()
        logger.info("find meeting:{}".format(len(meeting)))
        for meeting in meeting:
            uri = DeleteMeetingViewTest.url.format(meeting.id)
            self.client.delete(uri)
        self.clear_user()

    # noinspection SpellCheckingInspection
    def test_get_participants_welink_ok(self):
        user = self._setup()
        data = copy.deepcopy(CreateMeetingViewTest.data)
        data["sponsor"] = user.username
        self.client.post(CreateMeetingViewTest.url, data)
        meeting = self.get_meeting_by_username(user.username)
        ret = self.client.get(self.url.format(meeting.id))
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        self._teardown()

    def test_get_participants_zoom_ok(self):
        user = self._setup()
        data = copy.deepcopy(CreateMeetingViewTest.data)
        data["sponsor"] = user.username
        data["platform"] = "ZOOM"
        self.client.post(CreateMeetingViewTest.url, data)
        meeting = self.get_meeting_by_username(user.username)
        ret = self.client.get(self.url.format(meeting.id))
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        self._teardown()

    def test_get_participants_tencent_ok(self):
        user = self._setup()
        data = copy.deepcopy(CreateMeetingViewTest.data)
        data["sponsor"] = user.username
        data["platform"] = "TENCENT"
        self.client.post(CreateMeetingViewTest.url, data)
        meeting = self.get_meeting_by_username(user.username)
        ret = self.client.get(self.url.format(meeting.id))
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        self._teardown()


class GetMeetingDateViewTest(TestCommonMeeting):
    url = "/inner/v1/meeting/meeting/date/"

    def _setup(self):
        user = self.create_user()
        self.enable_client_auth(user.username)
        return user

    def test_get_meeting_date(self):
        ret = self.client.get(self.url)
        self.assertEqual(ret.status_code, status.HTTP_200_OK)

    def _teardown(self):
        meeting = self.get_meetings()
        logger.info("find meeting:{}".format(len(meeting)))
        for meeting in meeting:
            uri = DeleteMeetingViewTest.url.format(meeting.id)
            self.client.delete(uri)
        self.clear_user()


class GetMeetingPlatformViewTest(TestCommonMeeting):
    url = "/inner/v1/meeting/meeting/platform/?community={}"

    def _setup(self):
        user = self.create_user()
        self.enable_client_auth(user.username)
        return user

    def test_get_meeting_date(self):
        ret = self.client.get(self.url.format("openEuler"))
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
