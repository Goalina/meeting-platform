#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/8/16 14:45
# @Author  : Tom_zc
# @FileName: meeting_adapter.py
# @Software: PyCharm
from meeting.models import Meeting
from django.db.models import Q


class MeetingDao:
    dao = Meeting

    @classmethod
    def get_conflict_meeting(cls, community, platform, date, start_search, end_search, meeting_id=None):
        query_set = cls.dao.objects.filter(community=community,
                                           platform=platform,
                                           date=date,
                                           is_delete=0,
                                           is_cycle=False)
        query_set = query_set.filter(Q(cycle_date__start__lt=end_search, cycle_date__end__gt=start_search) |
                                     Q(start__lt=end_search, end__gt=start_search))
        if meeting_id is None:
            return query_set.values_list("host_id")
        return query_set.exclude(id=meeting_id).values_list("host_id")

    @classmethod
    def get_today_meeting_counts(cls, community, sponsor, date):
        return cls.dao.objects.filter(community=community, sponsor=sponsor, create_time__date=date).count()

    @classmethod
    def get_repeat_meeting_by_community_sponsor_date_start_counts(cls, community, group_name, sponsor, date, start):
        return cls.dao.objects.filter(community=community, group_name=group_name, sponsor=sponsor,
                                      date=date, start=start, is_delete=False, is_cycle=False).count()

    @classmethod
    def get_repeat_meeting_by_cycle_mid(cls, community, group_name, sponsor):
        return cls.dao.objects.filter(community=community, group_name=group_name, sponsor=sponsor,
                                      is_delete=False, is_cycle=True).values_list("mid", flat=True)

    @classmethod
    def get_queryset(cls):
        return cls.dao.objects.all()

    @classmethod
    def create(cls, **kwargs):
        return cls.dao.objects.create(**kwargs)

    @classmethod
    def get_by_id(cls, meeting_id):
        return cls.dao.objects.filter(id=meeting_id, is_delete=0).first()

    @classmethod
    def get_by_mid(cls, mid):
        return cls.dao.objects.filter(mid=mid, is_delete=0).first()

    @classmethod
    def get_by_mid_list(cls, mid_list):
        return cls.dao.objects.filter(mid__in=mid_list, is_delete=0).values()

    @classmethod
    def update_by_id(cls, meeting_id, **kwargs):
        return cls.dao.objects.filter(id=meeting_id, is_delete=0).update(**kwargs)

    @classmethod
    def update_bili_records_by_mid(cls, mid):
        return cls.dao.objects.filter(mid=mid, is_delete=0).update(bili_records=None)

    @classmethod
    def update_obs_records_by_mid(cls, mid):
        return cls.dao.objects.filter(mid=mid, is_delete=0).update(obs_records=None)

    @classmethod
    def delete_by_id(cls, meeting_id, sequence):
        return cls.dao.objects.filter(id=meeting_id, is_delete=0).update(is_delete=1,
                                                                         sequence=sequence,
                                                                         bili_records=None,
                                                                         obs_records=None)

    @classmethod
    def get_meeting_by_date(cls, community, start_date, end_date, end_time):
        start_and_end_date = Q(date__gt=start_date, date__lt=end_date)
        today = Q(date=end_date, end__lt=end_time)
        return cls.dao.objects.filter(is_delete=0, community=community). \
            filter().filter(start_and_end_date | today).all()

    @classmethod
    def get_meeting_by_obs_records(cls, community, obs_records, start_date, end_date):
        return cls.dao.objects.filter(is_delete=0, community=community,
                                      is_record=True, obs_records_id__in=obs_records). \
            filter(Q(date__gt=start_date) & Q(date__lte=end_date)).all()

    @classmethod
    def get_meeting_by_bili_records(cls, community, bili_records, start_date, end_date):
        return cls.dao.objects.filter(is_delete=0, community=community,
                                      is_record=True, bili_records_id__in=bili_records). \
            filter(Q(date__gt=start_date) & Q(date__lte=end_date)).all()
