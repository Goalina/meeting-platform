#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2025/7/1 9:34
# @Author  : Tom_zc
# @FileName: translate_adapter_impl.py
# @Software: PyCharm
import logging
import requests

from django.conf import settings

logger = logging.getLogger("log")


class TranslateAdapterImpl(object):
    def __init__(self, meeting):
        self.is_ignore = True
        if not settings.COMMUNITY_TRANSLATE:
            return
        self.is_ignore = False
        translate_info = settings.COMMUNITY_TRANSLATE[meeting]
        self._translate_url = translate_info["URL"]
        self._bucket_name = translate_info["BUCKET_NAME"]

    def translate(self, mid, sub_id, object_key):
        if self.is_ignore:
            return
        body = {
            "mid": mid,
            "sub_id": sub_id,
            "object_key": object_key,
            "bucket_key": self._bucket_name,
        }
        logger.info(body)
        logger.info(self._translate_url)
        resp = requests.post(self._translate_url, json=body, timeout=settings.REQUEST_TIMEOUT)
        if resp.status_code != 200:
            raise Exception("request meeting translate failed:{}/{}".format(resp.status_code, resp.content.decode()))
        logger.info("request meeting translate success:{}".format(mid))
