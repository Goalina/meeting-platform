#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2025/6/30 20:51
# @Author  : Tom_zc
# @FileName: meeting_records_obs_dao.py
# @Software: PyCharm


from meeting.models import MeetingObsRecords


class MeetingRecordsObsDao:
    _dao = MeetingObsRecords

    @classmethod
    def get_records_by_status(cls, status):
        return cls._dao.objects.filter(status=status).values_list("id", flat=True)

    @classmethod
    def get_by_mid(cls, mid):
        return cls._dao.objects.filter(mid=mid).first()

    @classmethod
    def update_by_mid(cls, mid, status, **kwargs):
        return cls._dao.objects.filter(id=mid).update(status=status, **kwargs)

    @classmethod
    def create(cls, status, mid):
        return cls._dao.objects.create(status=status, mid=mid)

    @classmethod
    def delete_by_mid(cls, mid):
        return cls._dao.objects.filter(mid=mid).delete()
