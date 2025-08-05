#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/8/26 11:16
# @Author  : Tom_zc
# @FileName: handle_recordings.py
# @Software: PyCharm
import os
import shutil
import logging
import time
import datetime
import traceback
from collections import defaultdict

from django.conf import settings
from django.core.management.base import BaseCommand
from django.forms import model_to_dict

from meeting_platform.utils.common import execute_cmd3
from meeting_platform.utils.customized.my_trimmer import trimmer_video
from meeting_platform.utils.file_stream import write_content
from meeting.domain.primitive.upload_status import UploadStatus
from meeting.infrastructure.adapter.bilibili_adapter_impl import BiliAdapterImpl
from meeting.infrastructure.adapter.meeting_adapter_impl.meeting_adapter_impl import MeetingAdapterImpl
from meeting.infrastructure.adapter.upload_adapter_impl.bili_upload_adapter_impl import BiliUploadAdapterImpl
from meeting.infrastructure.adapter.upload_adapter_impl.obs_upload_adapter_impl import ObsUploadAdapterImpl
from meeting.infrastructure.adapter.translate_adapter_impl import TranslateAdapterImpl
from meeting.infrastructure.dao.meeting_dao import MeetingDao
from meeting.infrastructure.dao.meeting_records_obs_dao import MeetingRecordsObsDao
from meeting.infrastructure.dao.meeting_records_bili_dao import MeetingRecordsBiliDao

logger = logging.getLogger("log")


class HandleRecording:
    meeting_dao = MeetingDao
    meeting_obs_records_dao = MeetingRecordsObsDao
    meeting_bili_records_dao = MeetingRecordsBiliDao

    def __init__(self, community):
        self.community = community
        self.translate_adapter_impl = TranslateAdapterImpl(community)
        self.meeting_adapter_impl = MeetingAdapterImpl()
        self.bili_adapter_impl = BiliAdapterImpl(community)
        self.upload_obs_adapter_impl = ObsUploadAdapterImpl
        self.upload_bili_adapter_impl = BiliUploadAdapterImpl

    # noinspection LongLine
    @staticmethod
    def _cover_content(topic, group_name, date, start_time, end_time):
        """get the cover html template"""
        content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>cover</title>
        </head>
        <body>
            <div style="display: inline-block; height: 688px; width: 1024px; text-align: center; background-image: url('cover.png')">
                <p style="font-size: 100px;margin-top: 150px; color: white"><b>{0}</b></p>
                <p style="font-size: 80px; margin: 0; color: white">SIG: {1}</p>
                <p style="font-size: 60px; margin: 0; color: white">Time: {2} {3}-{4}</p>
            </div>
        </body>
        </html>
        """.format(topic, group_name, date, start_time, end_time)
        return content

    def _get_video_path(self, meeting):
        """get video path in local file system"""
        video_path = self.meeting_adapter_impl.get_video(meeting)
        if not video_path:
            logger.error('[HandleRecording/_get_video_path]  {}/{}: video path could not be empty'.
                         format(self.community, meeting["mid"]))
            return
        if not os.path.exists(video_path):
            logger.error('[HandleRecording/_get_video_path]  {}/{}: video path could not be exist'.
                         format(self.community, meeting["mid"]))
            return
        if os.path.getsize(video_path) == 0:
            logger.error('[HandleRecording/_get_video_path] {}/{}: download but size is 0'.
                         format(self.community, meeting["mid"]))
            return
        return video_path

    def _get_video_cover_path(self, video_path, meeting):
        """get cover image"""
        # parse parameter
        html_path = video_path.replace('.mp4', '.html')
        image_path = video_path.replace('.mp4', '.png')
        mid = meeting["mid"]
        topic = meeting["topic"]
        group_name = meeting["group_name"]
        date = meeting["date"]
        start = meeting["start"]
        end = meeting["end"]
        community = meeting["community"]
        content = self._cover_content(topic, group_name, date, start, end)
        # write content to html
        write_content(html_path, content, model="w")
        if not os.path.exists(os.path.join(os.path.dirname(video_path), 'cover.png')):
            shutil.copy("meeting_platform/templates/image/{}/cover.png".format(community), os.path.dirname(video_path))
        execute_cmd3("wkhtmltoimage --enable-local-file-access {} {}".format(html_path, image_path))
        logger.info("[HandleRecording/_generate_cover] {}/{}: generate cover success".format(self.community, mid))
        if not os.path.exists(image_path):
            logger.error('[HandleRecording/_get_video_cover_path] {}/{}: fail to generate cover for meeting video'
                         .format(self.community, meeting["mid"]))
            return
        return image_path

    @staticmethod
    def _get_valid_query_range():
        cur_date = datetime.datetime.now()
        start_date = str(cur_date - datetime.timedelta(days=settings.BILI_UPLOAD_DATE))
        end_date = cur_date.strftime('%Y-%m-%d')
        return start_date, end_date

    def upload_obs(self):
        """upload all: get video --> upload obs"""
        cache_path = defaultdict(dict)
        meeting_obs_records = self.meeting_obs_records_dao.get_records_by_status(UploadStatus.INIT.value)
        start_date, end_date = self._get_valid_query_range()
        meeting_infos = self.meeting_dao.get_meeting_by_obs_records(self.community, meeting_obs_records, start_date,
                                                                    end_date)
        upload_mid = ",".join([str(i.mid) for i in meeting_infos])
        logger.info("[HandleRecording/upload_obs]: Find need to upload mid({}/{})".format(upload_mid, self.community))
        for meeting_obj in meeting_infos:
            try:
                meeting = model_to_dict(meeting_obj)
                video_path = self._get_video_path(meeting)
                if not video_path:
                    logger.info("[HandleRecording/upload_all]: Find empty video_path({})".format(meeting["mid"]))
                    continue
                cover_path = self._get_video_cover_path(video_path, meeting)
                if not cover_path:
                    logger.info("[HandleRecording/upload_all]: Find empty cover_path({})".format(meeting["mid"]))
                    continue
                video_path = trimmer_video(video_path, meeting["id"])
                video_object = self.upload_obs_adapter_impl(meeting).upload(video_path, cover_path)
                if not video_object:
                    raise Exception("upload obs failed")
                self.translate_adapter_impl.translate(meeting["mid"], video_object)
                self.meeting_obs_records_dao.update_by_mid(meeting_obj.bili_records.id,
                                                           status=UploadStatus.TRANSLATE.value)
                cache_path[meeting_obj.id] = {
                    "video_path": video_path,
                    "cover_path": cover_path,
                }
                logger.info("[HandleRecording/upload_obs]: handler success({})".format(meeting["mid"]))
            except Exception as e:
                logger.error("[HandleRecording/upload_obs] e:{}, traceback:{}".format(str(e), traceback.format_exc()))
            return cache_path

    def upload_bili(self, cache_path):
        """upload bili: get video --> upload bili"""
        meeting_obs_records = self.meeting_bili_records_dao.get_records_by_status(UploadStatus.INIT.value)
        start_date, end_date = self._get_valid_query_range()
        meeting_infos = self.meeting_dao.get_meeting_by_bili_records(self.community, meeting_obs_records, start_date,
                                                                     end_date)
        upload_mid = ",".join([str(i.mid) for i in meeting_infos])
        logger.info("[HandleRecording/upload_bili]: Find need to upload mid({}/{})".format(upload_mid, self.community))
        for meeting_obj in meeting_infos:
            try:
                meeting = model_to_dict(meeting_obj)
                if isinstance(cache_path, defaultdict) and meeting_obj.id in cache_path.keys():
                    video_path = cache_path[meeting_obj.id]["video_path"]
                    cover_path = cache_path[meeting_obj.id]["cover_path"]
                else:
                    video_path = self._get_video_path(meeting)
                    if not video_path:
                        logger.info("[HandleRecording/upload_bili]: Find empty video_path({})".format(meeting["mid"]))
                        continue
                    cover_path = self._get_video_cover_path(video_path, meeting)
                    if not cover_path:
                        logger.info("[HandleRecording/upload_bili]: Find empty cover_path({})".format(meeting["mid"]))
                        continue
                    video_path = trimmer_video(video_path, meeting["id"])
                vid = self.upload_bili_adapter_impl(meeting).upload(video_path, cover_path, return_replay_url=False)
                if not vid:
                    raise Exception("upload bili failed")
                logger.info("waiting the vid:{} pass".format(vid))
                while True:
                    all_videos = self.bili_adapter_impl.search_all_videos()
                    if vid in all_videos:
                        break
                    logger.info("video:{} not passed".format(vid))
                    time.sleep(300)
                replay_url = self.bili_adapter_impl.get_replay_url(vid)
                self.meeting_bili_records_dao.update_records(meeting.meeting_obj.id,
                                                             status=UploadStatus.FINISH.value,
                                                             replay_url=replay_url)
            except Exception as e:
                logger.error("[HandleRecording/upload_bili] e:{}, traceback:{}".format(str(e), traceback.format_exc()))


def work_flow(handle_recording: HandleRecording):
    """按照社区进行分类操作
        1.上传OBS
        2.上传bilibili
    :param handle_recording:HandleRecording
    :return:
    """
    try:
        cache_path = handle_recording.upload_obs()
        handle_recording.upload_bili(cache_path)
    except Exception as e:
        logger.error("[work_flow] e:{}, traceback:{}".format(e, traceback.format_exc()))


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info('-' * 20 + ' start to handler recordings' + '-' * 20)
        logger.info('[handle] find community: {}'.format(",".join(settings.COMMUNITY_SUPPORT)))
        try:
            for i in settings.COMMUNITY_SUPPORT:
                work_flow(HandleRecording(i))
            logger.info('-' * 20 + 'All done' + '-' * 20)
        except Exception as e:
            logger.error("[handle_recordings/handle] err:{}, traceback:{}".format(str(e), traceback.format_exc()))
