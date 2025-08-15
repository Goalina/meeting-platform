#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2025/8/15 10:54
# @Author  : Tom_zc
# @FileName: core_operators.py
# @Software: PyCharm
import datetime
import calendar
import logging

from meeting.domain.primitive.cycle_type import CycleType

logger = logging.getLogger("log")


def get_cycle_date_by_policy(meeting):
    """get the cycle date by policy"""
    meeting_date_list = list()
    start_date = datetime.datetime.strptime(meeting["cycle_start_date"], "%Y-%m-%d")
    end_date = datetime.datetime.strptime(meeting["cycle_end_date"], "%Y-%m-%d")
    if meeting["cycle_type"] == CycleType.DAY:
        while start_date <= end_date:
            start_date += datetime.timedelta(days=meeting["cycle_interval"])
            meeting_date_list.append(
                {
                    "date": start_date,
                    "start": meeting["cycle_start"],
                    "end": meeting["cycle_end"]
                }
            )
    elif meeting["cycle_type"] == CycleType.Week:
        for wd in meeting["cycle_point"]:
            current = start_date + datetime.timedelta(days=(wd - (start_date.weekday() + 1) + 7) % 7)
            while current <= end_date:
                meeting_date_list.append(
                    {
                        "date": current,
                        "start": meeting["cycle_start"],
                        "end": meeting["cycle_end"]
                    }
                )
                current += datetime.timedelta(weeks=1)
    elif meeting["cycle_type"] == CycleType.Month:
        # 从月份第一天开始
        current_month = start_date.replace(day=1)
        while current_month <= end_date:
            year, month = current_month.year, current_month.month
            # 获取当月最后一天
            last_day = calendar.monthrange(year, month)[1]
            for day in meeting["cycle_point"]:
                # 处理无效日期
                meeting_day = min(day, last_day)
                meeting_date = datetime.datetime(year, month, meeting_day)
                # 如果早于start_time，跳过
                if meeting_date < start_date:
                    continue
                if meeting_date <= end_date:
                    meeting_date_list.append(
                        {
                            "date": meeting_date,
                            "start": meeting["cycle_start"],
                            "end": meeting["cycle_end"]
                        }
                    )
            if month == 12:
                current_month = datetime.datetime(year + 1, 1, 1)
            else:
                current_month = datetime.datetime(year, month + 1, 1)
        else:
            logger.info("invalid cycle type")
    return meeting_date_list
