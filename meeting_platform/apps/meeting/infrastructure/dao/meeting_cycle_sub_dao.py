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
    def get_by_mid(cls, mid):
        return cls._dao.objects.filter(mid=mid).all().values()

    @classmethod
    def get_by_date(cls, date, start_search, end_search):
        return cls._dao.objects.filter(date=date, start__gte=start_search, end__lte=end_search).all().values_list("mid")

    @classmethod
    def create(cls, **kwargs):
        return cls._dao.objects.create(**kwargs)

    @classmethod
    def get_count_by_mid_and_sub_id(cls, mid, sub_id):
        return cls._dao.objects.filter(mid=mid, sub_id=sub_id).count()

    @classmethod
    def get_by_mid_and_sub_id(cls, mid, sub_id):
        return cls._dao.objects.filter(mid=mid, sub_id=sub_id).first()

    @classmethod
    def delete_by_mid_and_sub_id(cls, mid, sub_id):
        return cls._dao.objects.filter(mid=mid, sub_id=sub_id).delete()

    @classmethod
    def delete_by_mid(cls, mid):
        return cls._dao.objects.filter(mid=mid).delete()

    @classmethod
    def update_by_mid_and_sub_id(cls, mid, sub_id, **kwargs):
        return cls._dao.objects.filter(mid=mid, sub_id=sub_id).update(kwargs)

    @classmethod
    def delete_by_id(cls, cycle_dao_id):
        return cls._dao.objects.filter(id=cycle_dao_id).delete()
