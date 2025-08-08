#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/8/16 11:16
# @Author  : Tom_zc
# @FileName: models.py.py
# @Software: PyCharm
from django.contrib.auth.models import AbstractUser
from django.db import models

from meeting.domain.primitive.upload_status import UploadStatus
from meeting.domain.primitive.cycle_type import CycleType


class User(AbstractUser):
    """user model"""

    class Meta:
        db_table = "user"
        verbose_name = db_table
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username


class MeetingBiliRecords(models.Model):
    """meeting obs records"""
    mid = models.CharField(verbose_name='会议id', max_length=32)
    status = models.SmallIntegerField(verbose_name="上传状态", choices=UploadStatus.to_tuple(), default=0)
    replay_url = models.CharField(verbose_name='回放会议url', max_length=128, null=True, blank=True)

    objects = models.Manager()

    class Meta:
        db_table = "meetings_records_bili"
        verbose_name = db_table
        verbose_name_plural = verbose_name

    def __str__(self):
        return "{}".format(self.id)


class MeetingObsRecords(models.Model):
    """meeting bili records"""
    mid = models.CharField(verbose_name='会议id', max_length=32)
    status = models.SmallIntegerField(verbose_name="上传状态", choices=UploadStatus.to_tuple(), default=0)
    text_vtt_url = models.CharField(verbose_name='文本vtt地址', max_length=255, null=True, blank=True)
    text_json_url = models.CharField(verbose_name='文本json地址', max_length=255, null=True, blank=True)
    text_video_url = models.CharField(verbose_name='文本video地址', max_length=255, null=True, blank=True)

    objects = models.Manager()

    class Meta:
        db_table = "meetings_records_obs"
        verbose_name = db_table
        verbose_name_plural = verbose_name

    def __str__(self):
        return "{}".format(self.id)


class MeetingCycleDate(models.Model):
    """meeting cycle date model"""
    mid = models.CharField(verbose_name='会议id', max_length=32)
    start_date = models.CharField(verbose_name='会议开始日期', max_length=32)
    end_date = models.CharField(verbose_name='会议结束日期', max_length=32)
    start = models.CharField(verbose_name='会议开始时间', max_length=32)
    end = models.CharField(verbose_name='会议结束时间', max_length=32)
    cycle_type = models.SmallIntegerField(verbose_name="周期类型", choices=CycleType.to_tuple())
    interval = models.IntegerField(verbose_name="子会议时间间隔")
    point = models.IntegerField(verbose_name="周期内的会员召开时间", null=True, blank=True)

    objects = models.Manager()

    class Meta:
        db_table = "meetings_cycle_date"
        verbose_name = db_table
        verbose_name_plural = verbose_name

    def __str__(self):
        return "{}/{}/{}/{}".format(self.mid, self.cycle_type, self.start_date, self.end_date)


class MeetingCycleSubMeeting(models.Model):
    """meeting cycle sub meeting model"""
    mid = models.CharField(verbose_name='会议id', max_length=32)
    sub_id = models.CharField(verbose_name='子会议的ID', max_length=32)
    date = models.CharField(verbose_name='会议日期', max_length=32)
    start = models.CharField(verbose_name='会议开始时间', max_length=32)
    end = models.CharField(verbose_name='会议结束时间', max_length=32)

    objects = models.Manager()

    class Meta:
        db_table = "meetings_cycle_sub_meeting"
        verbose_name = db_table
        verbose_name_plural = verbose_name

    def __str__(self):
        return "{}/{}/{}".format(self.mid, self.sub_id, self.date)


class Meeting(models.Model):
    """meeting model"""
    sponsor = models.CharField(verbose_name='发起者', max_length=64)
    group_name = models.CharField(verbose_name='发起者所属SIG', max_length=64)
    community = models.CharField(verbose_name="发起者所在社区", max_length=16)
    topic = models.CharField(verbose_name='会议主题', max_length=128)
    platform = models.CharField(verbose_name="会议所属平台", max_length=16)
    is_cycle = models.BooleanField(verbose_name="是否周期性会议", default=False)
    date = models.CharField(verbose_name='会议日期', max_length=32)
    start = models.CharField(verbose_name='会议开始时间', max_length=32)
    end = models.CharField(verbose_name='会议结束时间', max_length=32)
    cycle_date = models.OneToOneField(MeetingCycleDate, on_delete=models.CASCADE, null=True, blank=True)
    agenda = models.TextField(verbose_name='会议议程', default='', null=True, blank=True)
    etherpad = models.CharField(verbose_name='会议纪要etherpad', max_length=256, null=True, blank=True)
    email_list = models.TextField(verbose_name='邮件列表', null=True, blank=True)
    host_id = models.EmailField(verbose_name='会议host_id', null=True, blank=True)
    mid = models.CharField(verbose_name='会议id', max_length=32)
    m_mid = models.CharField(verbose_name='腾讯会议id', max_length=32, null=True, blank=True)
    join_url = models.CharField(verbose_name='进入会议url', max_length=128, null=True, blank=True)
    is_record = models.BooleanField(verbose_name="是否录制", default=False)
    obs_records = models.OneToOneField(MeetingObsRecords, on_delete=models.SET_NULL, null=True, blank=True)
    bili_records = models.OneToOneField(MeetingBiliRecords, on_delete=models.SET_NULL, null=True, blank=True)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True, null=True, blank=True)
    update_time = models.DateTimeField(verbose_name='修改时间', null=True, blank=True)
    sequence = models.IntegerField(verbose_name='修改次数', default=1)
    is_delete = models.BooleanField(verbose_name='是否删除', default=False)

    objects = models.Manager()

    class Meta:
        db_table = "meetings"
        verbose_name = db_table
        verbose_name_plural = verbose_name

    def __str__(self):
        return "{}/{}/{}".format(self.community, self.mid, self.topic)


class MeetingParticipants(models.Model):
    """meeting participants for collect center"""
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    participants = models.TextField(verbose_name='会议议程', default='', null=True, blank=True)

    objects = models.Manager()

    class Meta:
        db_table = "meetings_participants"
        verbose_name = db_table
        verbose_name_plural = verbose_name

    def __str__(self):
        return "{}".format(self.meeting)


class MeetingCache(models.Model):
    """meeting cache for the cronjob scan_upload_meetings"""
    meeting_id = models.CharField(verbose_name='会议id', max_length=32)
    vid = models.CharField(verbose_name='B站回放会议id', max_length=128, null=True, blank=True)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True, null=True, blank=True)

    objects = models.Manager()

    class Meta:
        db_table = "meetings_cache"
        verbose_name = db_table
        verbose_name_plural = verbose_name

    def __str__(self):
        return "{}/{}".format(self.meeting_id, self.vid)
