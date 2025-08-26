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
        return cls._dao.objects.filter(status=status).values_list("meeting_id", flat=True)

    @classmethod
    def get_records_by_status_and_mid(cls, mid, status):
        return cls._dao.objects.filter(mid=mid, status=status).values_list("sub_id", flat=True)

    @classmethod
    def get_by_mid(cls, mid):
        return cls._dao.objects.filter(mid=mid).values()

    @classmethod
    def get_by_id(cls, cur_id):
        return cls._dao.objects.filter(id=cur_id)

    @classmethod
    def update_by_mid(cls, mid, sub_id, status, **kwargs):
        queryset = cls._dao.objects.filter(mid=mid)
        if sub_id:
            queryset = queryset.filter(sub_id=sub_id)
        return queryset.update(status=status, **kwargs)

    @classmethod
    def create(cls, status, mid, sub_id, meeting_id):
        return cls._dao.objects.create(status=status, mid=mid, sub_id=sub_id, meeting_id=meeting_id)

    @classmethod
    def delete_by_mid_and_sub_id(cls, mid, sub_id):
        return cls._dao.objects.filter(mid=mid, sub_id=sub_id).all().delete()

    @classmethod
    def delete_by_mid(cls, mid):
        return cls._dao.objects.filter(mid=mid).all().delete()
