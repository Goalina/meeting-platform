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
    def get_by_date(cls, date):
        return cls._dao.objects.filter(date=date)

    @classmethod
    def get_by_date_range(cls, community, platform, date, start_search, end_search, mid):
        queryset = cls._dao.objects.filter(community=community,
                                           platform=platform,
                                           date=date,
                                           start__lt=start_search,
                                           end__gt=end_search)
        if mid is None:
            return queryset.all().values_list("host_id")
        else:
            return queryset.exclude(mid=mid).all().values_list("host_id")

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
    def delete_by_mid(cls, mid):
        return cls._dao.objects.filter(mid=mid).delete()

    @classmethod
    def update_by_mid_and_sub_id(cls, mid, sub_id, **kwargs):
        return cls._dao.objects.filter(mid=mid, sub_id=sub_id).update(**kwargs)
