#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/8/16 11:22
# @Author  : Tom_zc
# @FileName: inner.py
# @Software: PyCharm


from django.urls import path

from meeting.controller.inner import MeetingView, SingleMeetingView, MeetingParticipantsView, \
    MeetingPlatformView, MeetingDateView, MeetingTextCallBack, SingleSubMeetingView

urlpatterns = [
    path('meeting/', MeetingView.as_view()),                                    # 预定会议/会议列表
    path('meeting/<int:id>/', SingleMeetingView.as_view()),                     # 修改/删除/查询会议/周期性会议
    path('meeting/sub/<str:sub_id>/', SingleSubMeetingView.as_view()),          # 修改/删除周期性会议的子会议
    path('meeting/date/', MeetingDateView.as_view()),                           # 获取会议时间（官网）
    path('meeting/participants/<int:id>/', MeetingParticipantsView.as_view()),  # 查询会议参与人
    path('meeting/platform/', MeetingPlatformView.as_view()),                   # 获取会议类型

    path('meeting/meeting_text/callback/', MeetingTextCallBack.as_view())       # 文字翻译的回调地址
]
