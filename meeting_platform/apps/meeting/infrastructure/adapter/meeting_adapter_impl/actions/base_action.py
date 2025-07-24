#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/6/19 16:40
# @Author  : Tom_zc
# @FileName: base_action.py
# @Software: PyCharm


class BaseAction:
    function_action = None
    community = None


class CreateAction(BaseAction):
    function_action = "create"


class CreateCycleAction(BaseAction):
    function_action = "create_cycle"


class UpdateAction(BaseAction):
    function_action = "update"


class UpdateCycleAction(BaseAction):
    function_action = "update_cycle"


class UpdateCycleSubAction(BaseAction):
    function_action = "update_cycle_sub"


class DeleteAction(BaseAction):
    function_action = "delete"


class DeleteCycleAction(BaseAction):
    function_action = "delete_cycle"


class DeleteCycleSubAction(BaseAction):
    function_action = "delete_cycle_sub"


class GetParticipantsAction(BaseAction):
    function_action = "get_participants"


class GetVideoAction(BaseAction):
    function_action = "get_video"
