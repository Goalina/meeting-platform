#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/7/15 10:53
# @Author  : Tom_zc
# @FileName: kafka_client.py
# @Software: PyCharm
import datetime
import logging
from abc import ABC

from django.conf import settings

from meeting_platform.utils.client.kafka_client import KafKaClient
from meeting_platform.utils.common import func_retry
from meeting.domain.repository.message_adapter import MessageAdapter

logger = logging.getLogger("log")


class MessageKafKaAdapterImpl(MessageAdapter, ABC):
    def get_client(self, meeting):
        kafka_info = settings.COMMUNITY_KAFKA.get(meeting["community"])
        if kafka_info is None:
            return None
        else:
            return kafka_info


class CreateMessageKafKaAdapterImpl(MessageKafKaAdapterImpl):

    @func_retry()
    def send_message(self, meeting):
        kafka_info = self.get_client(meeting)
        if not kafka_info or not isinstance(kafka_info, dict):
            logger.info("[CreateMessageAdapterImpl] {} kafka_info config is empty, Please ignore."
                        .format(meeting["community"]))
            return
        if not kafka_info.get("KAFKA_TOPIC") or not kafka_info.get("KAFKA_SERVER"):
            logger.info("[CreateMessageAdapterImpl] {} kafka config is empty, Please ignore."
                        .format(meeting["community"]))
            return
        if "cycle_type" in meeting.keys():
            meeting["cycle_type"] = meeting["cycle_type"].des
        with KafKaClient(kafka_info) as client:
            data = {
                "action": "create_meeting",
                "msg": meeting
            }
            client.send_msg(kafka_info["KAFKA_TOPIC"], data)
            logger.info("[CreateMessageAdapterImpl] {}/{}/{}/{}/{} send create kafka msg success".format(
                meeting["community"], meeting["platform"], meeting["topic"], meeting["mid"], meeting["id"]))


class UpdateMessageKafKaAdapterImpl(MessageKafKaAdapterImpl):

    @func_retry()
    def send_message(self, meeting):
        kafka_info = self.get_client(meeting)
        if not kafka_info or not isinstance(kafka_info, dict):
            logger.info("[UpdateMessageKafKaAdapterImpl] {} kafka_info config is empty, Please ignore."
                        .format(meeting["community"]))
            return
        if not kafka_info.get("KAFKA_TOPIC") or not kafka_info.get("KAFKA_SERVER"):
            logger.info("[UpdateMessageKafKaAdapterImpl] {} kafka config is empty, Please ignore."
                        .format(meeting["community"]))
            return
        if isinstance(meeting.get("update_time"), datetime.datetime):
            meeting["update_time"] = meeting["update_time"].strftime("%Y-%m-%d %H:%M")
        if "cycle_type" in meeting.keys():
            meeting["cycle_type"] = meeting["cycle_type"].des
        with KafKaClient(kafka_info) as client:
            data = {
                "action": "update_meeting",
                "msg": meeting
            }
            client.send_msg(kafka_info["KAFKA_TOPIC"], data)
            logger.info("[UpdateMessageKafKaAdapterImpl] {}/{}/{}/{}/{} send update kafka msg success".format(
                meeting["community"], meeting["platform"], meeting["topic"], meeting["mid"], meeting["id"]))


class DeleteMessageKafKaAdapterImpl(MessageKafKaAdapterImpl):

    @func_retry()
    def send_message(self, meeting):
        kafka_info = self.get_client(meeting)
        if not kafka_info or not isinstance(kafka_info, dict):
            logger.info("[DeleteMessageKafKaAdapterImpl] {} kafka_info config is empty, Please ignore."
                        .format(meeting["community"]))
            return
        if not kafka_info.get("KAFKA_TOPIC") or not kafka_info.get("KAFKA_SERVER"):
            logger.info("[DeleteMessageKafKaAdapterImpl] {} kafka config is empty, Please ignore."
                        .format(meeting["community"]))
            return
        if isinstance(meeting.get("create_time"), datetime.datetime):
            meeting["create_time"] = meeting["create_time"].strftime("%Y-%m-%d %H:%M")
        if isinstance(meeting.get("update_time"), datetime.datetime):
            meeting["update_time"] = meeting["update_time"].strftime("%Y-%m-%d %H:%M")
        if "cycle_type" in meeting.keys():
            meeting["cycle_type"] = meeting["cycle_type"].des
        with KafKaClient(kafka_info) as client:
            data = {
                "action": "delete_meeting",
                "msg": meeting
            }
            client.send_msg(kafka_info["KAFKA_TOPIC"], data)
            logger.info("[DeleteMessageKafKaAdapterImpl] {}/{}/{}/{}/{} send delete kafka msg success".format(
                meeting["community"], meeting["platform"], meeting["topic"], meeting["mid"], meeting["id"]))
