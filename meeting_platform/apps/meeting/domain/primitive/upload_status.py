#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/8/27 11:50
# @Author  : Tom_zc
# @FileName: upload_status.py
# @Software: PyCharm
from meeting_platform.utils.base_enum import EnumBase


class UploadStatus(EnumBase):
    """上传状态"""
    INIT = (0, '初始化')
    TRANSLATE = (1, '完成请求翻译')
    FINISH = (10, '已经上传完成')
