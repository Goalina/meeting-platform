#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2025/3/19 9:56
# @Author  : Tom_zc
# @FileName: handle_meeting.py
# @Software: PyCharm

import logging
import traceback
import datetime
from multiprocessing.dummy import Pool as ThreadPool

from django.conf import settings
from django.core.management.base import BaseCommand
from django.forms import model_to_dict

from meeting.infrastructure.adapter.meeting_adapter_impl.meeting_adapter_impl import MeetingAdapterImpl
from meeting.infrastructure.dao import meeting_dao, meeting_participants_dao

logger = logging.getLogger("log")


class HandleMeeting:
    meeting_dao = meeting_dao.MeetingDao
    meeting_participants_dao = meeting_participants_dao.MeetingParticipantsDao
    meeting_adapter_impl = MeetingAdapterImpl()

    def __init__(self, community):
        self.community = community

    @staticmethod
    def _get_valid_query_range():
        cur_date = datetime.datetime.now()
        start_date = str(cur_date - datetime.timedelta(days=settings.QUERY_MEETING_DATE))
        end_date = cur_date.strftime('%Y-%m-%d')
        hour = f"{cur_date.hour:02}"
        minute = f"{cur_date.minute:02}"
        return start_date, end_date, f"{hour}:{minute}"

    def _get_over_meeting(self):
        start_date, end_date, end_time = self._get_valid_query_range()
        return self.meeting_dao.get_meeting_by_date(self.community, start_date, end_date, end_time)

    def refresh_meeting_participants(self):
        meetings = self._get_over_meeting()
        for meeting in meetings:
            meeting_info = self.meeting_participants_dao.get(meeting.id)
            if not meeting_info:
                logger.info("start to handle meeting:{}".format(meeting.id))
                meeting_participants = self.meeting_adapter_impl.get_participants(model_to_dict(meeting))
                if meeting_participants.get("participants"):
                    participants = [user["name"] for user in meeting_participants["participants"]]
                    deduplication_participants = list(set(participants))
                    data = {
                        "meeting": meeting,
                        "participants": ",".join(deduplication_participants)
                    }
                    self.meeting_participants_dao.create(**data)


def work_flow(handle_meeting: HandleMeeting):
    try:
        handle_meeting.refresh_meeting_participants()
    except Exception as e:
        logger.error("[handle_meeting] work_flow:{}, traceback:{}".format(str(e), traceback.format_exc()))


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info('-' * 20 + ' start to handle meeting' + '-' * 20)
        logger.info('[handle] find community: {}'.format(",".join(settings.COMMUNITY_SUPPORT)))
        try:
            handler_recording_communities = [HandleMeeting(i) for i in settings.COMMUNITY_SUPPORT]
            pool = ThreadPool()
            pool.map(work_flow, handler_recording_communities)
            pool.close()
            pool.join()
            logger.info('-' * 20 + 'All done' + '-' * 20)
        except Exception as e:
            logger.error("[handle_recordings/handle] err:{}, traceback:{}".format(str(e), traceback.format_exc()))
