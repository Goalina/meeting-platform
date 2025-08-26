#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2025/7/1 14:15
# @Author  : Tom_zc
# @FileName: obs_records_app.py
# @Software: PyCharm
from meeting.domain.primitive.upload_status import UploadStatus
from meeting.infrastructure.dao.meeting_dao import MeetingDao
from meeting.infrastructure.dao.meeting_records_obs_dao import MeetingRecordsObsDao

from meeting_platform.utils.ret_api import MyValidationError
from meeting_platform.utils.ret_code import RetCode


class OBSRecordsApp:
    _meeting_obs_records_dao = MeetingRecordsObsDao
    _meeting_dao = MeetingDao

    def update_by_mid(self, meeting_info):
        meeting_obj = self._meeting_dao.get_by_mid(meeting_info["mid"])
        if not meeting_obj:
            raise MyValidationError(RetCode.STATUS_MEETING_NOT_EXIST)
        mid, sub_id = None, None
        if "mid" in meeting_info.keys():
            mid = meeting_info.pop("mid")
        if "sub_id" in meeting_info.keys():
            sub_id = meeting_info.pop("sub_id")
        return self._meeting_obs_records_dao.update_by_mid(mid,
                                                           sub_id,
                                                           UploadStatus.FINISH.value,
                                                           **meeting_info)
