#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/7/9 20:29
# @Author  : Tom_zc
# @FileName: wk_action.py
# @Software: PyCharm
from dataclasses import dataclass

from meeting.infrastructure.adapter.meeting_adapter_impl.actions.base_action import CreateAction, \
    UpdateAction, DeleteAction, DeleteCycleAction, DeleteCycleSubAction, GetParticipantsAction, \
    GetVideoAction, CreateCycleAction, UpdateCycleAction, UpdateCycleSubAction


@dataclass
class WkCreateAction(CreateAction):
    date: str
    start: str
    end: str
    topic: str
    is_record: bool


@dataclass
class WkCreateCycleAction(CreateCycleAction):
    start_date: str
    end_date: str
    start: str
    end: str
    cycle_type: str
    interval: int
    point: [int]
    topic: str
    is_record: bool


@dataclass
class WkUpdateAction(UpdateAction):
    mid: str
    date: str
    start: str
    end: str
    topic: str
    is_record: bool


@dataclass
class WkUpdateCycleAction(UpdateCycleAction):
    mid: str
    start_date: str
    end_date: str
    start: str
    end: str
    cycle_type: str
    interval: int
    point: [int]
    topic: str
    is_record: bool


@dataclass
class WkUpdateCycleSubAction(UpdateCycleSubAction):
    mid: str
    sub_id: str
    date: str
    start: str
    end: str


@dataclass
class WkDeleteAction(DeleteAction):
    mid: str


@dataclass
class WkDeleteCycleAction(DeleteCycleAction):
    mid: str


@dataclass
class WkDeleteCycleSubAction(DeleteCycleSubAction):
    mid: str
    sub_id: str


@dataclass
class WkGetParticipantsAction(GetParticipantsAction):
    mid: str
    date: str
    start: str
    end: str


@dataclass
class WkGetVideo(GetVideoAction):
    mid: str
    date: str
    start: str
    end: str
