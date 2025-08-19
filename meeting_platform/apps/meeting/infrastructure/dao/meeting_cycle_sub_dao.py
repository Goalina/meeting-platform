#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2025/7/23 15:18
# @Author  : Tom_zc
# @FileName: meeting_cycle_sub_dao.py
# @Software: PyCharm


from meeting.models import MeetingCycleSubMeeting


class MeetingCycleSubMeetingDao:
    _dao = MeetingCycleSubMeeting

    @classmethod
    def get_all(cls):
        return cls._dao.objects.all()

    @classmethod
    def get_by_mid(cls, mid):
        return cls._dao.objects.filter(mid=mid).all().values()

    @classmethod
    def get_by_date_range(cls, start_date, end_date, mid):
        return cls._dao.objects.filter(date__gte=start_date, date__lte=end_date, mid=mid).values_list("date", flat=True)

    @classmethod
    def create(cls, **kwargs):
        return cls._dao.objects.create(**kwargs)

    @classmethod
    def get_by_mid_and_sub_id(cls, mid, sub_id):
        return cls._dao.objects.filter(mid=mid, sub_id=sub_id).first()

    @classmethod
    def get_by_sub_id(cls, sub_id):
        return cls._dao.objects.filter(sub_id=sub_id).first()

    @classmethod
    def delete_by_mid_and_sub_id(cls, mid, sub_id):
        return cls._dao.objects.filter(mid=mid, sub_id=sub_id).delete()

    @classmethod
    def delete_by_mid(cls, mid, cur_date_str):
        return cls._dao.objects.filter(mid=mid, date__gt=cur_date_str).delete()

    @classmethod
    def update_by_mid_and_sub_id(cls, mid, sub_id, **kwargs):
        return cls._dao.objects.filter(mid=mid, sub_id=sub_id).update(**kwargs)
