#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2025/7/16 15:00
# @Author  : Tom_zc
# @FileName: cycle_type.py
# @Software: PyCharm


import logging

from meeting_platform.utils.base_enum import EnumBase
from meeting_platform.utils.ret_api import MyValidationError
from meeting_platform.utils.ret_code import RetCode

logger = logging.getLogger("log")


class CycleType(EnumBase):
    DAY = (0, 'Day')
    Week = (1, 'Week')
    Month = (2, 'Month')

    @classmethod
    def check_value(cls, value):
        value = int(value)
        if value not in [cycle_type.value for cycle_type in cls]:
            logger.error("receive the invalid value:{}".format(value))
            raise MyValidationError(RetCode.STATUS_PARAMETER_ERROR)
        return CycleType(value)
