#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/8/22 20:18
# @Author  : Tom_zc
# @FileName: kafka_client.py
# @Software: PyCharm
import json
import ssl

from kafka import KafkaProducer
from django.conf import settings


class KafKaClient:
    def __init__(self, kafka_info):
        server = kafka_info["KAFKA_SERVER"]
        context = ssl.create_default_context()
        context.load_verify_locations(cadata=settings.KAFKA_CRT_CONTENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_REQUIRED
        self.client = KafkaProducer(
            bootstrap_servers=server,
            security_protocol="SASL_SSL",
            sasl_mechanism='PLAIN',
            sasl_plain_username=kafka_info["KAFKA_USERNAME"],
            sasl_plain_password=kafka_info["KAFKA_PASSWORD"],
            ssl_check_hostname=False,
            ssl_context=context,
            value_serializer=lambda v: json.dumps(v).encode()
        )

    def __enter__(self):
        return self

    def send_msg(self, topic, msg):
        self.client.send(topic, msg)
        self.client.flush()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            self.client.close(timeout=180)
