#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2025/4/22 15:56
# @Author  : Tom_zc
# @FileName: audit_client.py
# @Software: PyCharm
import logging
import requests
from django.conf import settings

logger = logging.getLogger("log")


class AuditClient:
    def __init__(self, url=None, token=None, audit_type="OFFICIAL_WEBSITE"):
        if not url and settings.COMMUNITY_AUDIT is not None:
            self._url = settings.COMMUNITY_AUDIT["URL"]
        else:
            self._url = url
        if not token and settings.COMMUNITY_AUDIT is not None:
            self._token = settings.COMMUNITY_AUDIT["TOKEN"]
        else:
            self._token = token
        self._audit_type = audit_type

    def _post_audit(self, content):
        headers = {
            "Content-Type": "application/json",
            "Token": self._token,
        }
        data = {
            "type": self._audit_type,
            "text": content
        }
        resp = requests.post(url=self._url, headers=headers, json=data, timeout=settings.REQUEST_TIMEOUT)
        if not str(resp.status_code).startswith("20"):
            raise Exception("request audit:{}, and error msg:{}".format(str(resp.status_code), resp.content.decode()))
        return resp.json()

    def check_content_ok(self, content):
        if self._url is None or self._token is None:
            logger.info("AuditClient the url and token is not config")
            return True
        json_data = self._post_audit(content)
        return json_data["data"]["result"] == "pass"
