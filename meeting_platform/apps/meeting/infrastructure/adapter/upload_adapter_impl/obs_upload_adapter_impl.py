#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/8/26 15:03
# @Author  : Tom_zc
# @FileName: obs_upload_adapter_impl.py
# @Software: PyCharm
import os
import datetime
import logging

from django.conf import settings

from meeting_platform.utils.common import func_retry
from meeting.domain.repository.upload_adapter import UploadAdapter
from meeting.infrastructure.adapter.obs_adapter_impl import ObsAdapterImp

logger = logging.getLogger("log")


# noinspection PyMethodMayBeStatic
class ObsUploadAdapterImpl(UploadAdapter):
    def __init__(self, meeting):
        super(ObsUploadAdapterImpl, self).__init__(meeting)
        obs_info = settings.COMMUNITY_OBS[meeting["community"]]
        self.obs_adapter_imp = ObsAdapterImp(obs_info["AK"], obs_info["SK"], obs_info["ENDPOINT"])
        self.endpoint = obs_info["ENDPOINT"]
        self.bucket = obs_info["BUCKET"]

    def _get_obs_video_object(self):
        mid = self.meeting["mid"]
        date = self.meeting["date"]
        group_name = self.meeting["group_name"]
        community = self.meeting["community"]
        month = datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%b').lower()
        return '{0}/{1}/{2}/{3}/{3}.mp4'.format(community, group_name, month, mid)

    def _get_obs_cover_object(self, video_object):
        return video_object.replace('.mp4', '.png')

    def _get_obs_video_download_url(self, obs_endpoint, bucket_name, video_object):
        return 'https://{}.{}/{}??response-content-disposition=attachment'.format(bucket_name, obs_endpoint,
                                                                                  video_object)

    def _get_size_of_file(self, file_path):
        if not os.path.exists(file_path):
            logger.error('Could not get size of a non exist file: {}'.format(file_path))
            return
        return os.path.getsize(file_path)

    def _generate_obs_metadata(self, video_object, video_path):
        date = self.meeting["date"]
        start = self.meeting["start"]
        end = self.meeting["end"]
        start_time = date + 'T' + start + ':00Z'
        end_time = date + 'T' + end + ':00Z'
        download_url = self._get_obs_video_download_url(self.endpoint, self.bucket, video_object)
        download_file_size = self._get_size_of_file(video_path)
        metadata = {
            "meeting_id": self.meeting["mid"],
            "meeting_topic": self.meeting["topic"],
            "community": self.meeting["community"],
            "sig": self.meeting["group_name"],
            "agenda": self.meeting["agenda"],
            "record_start": start_time,
            "record_end": end_time,
            "download_url": download_url,
            "total_size": download_file_size,
            "attenders": []
        }
        return metadata

    @func_retry()
    def upload(self, video_path, cover_path):
        logger.info("start to upload to obs...")
        # 1.upload the video
        video_object = self._get_obs_video_object()
        metadata = self._generate_obs_metadata(video_object, video_path)
        upload_video_res = self.obs_adapter_imp.upload_file(self.bucket, video_object, video_path, metadata)
        if upload_video_res.get('status') != 200:
            logger.error('[ObsUploadAdapterImpl/upload] {}/{}: fail to upload video to OBS, the reason is {}'.
                         format(self.meeting["community"], self.meeting["mid"], upload_video_res))
            return
        if not isinstance(upload_video_res, dict) or 'status' not in upload_video_res.keys():
            logger.error('[ObsUploadAdapterImpl/upload] {}/{} Unexpected upload video result to OBS: {}'.
                         format(self.meeting["community"], self.meeting["mid"], upload_video_res))
            return
        # 2.upload the cover png
        upload_cover_res = self.obs_adapter_imp.upload_file(self.bucket,
                                                            self._get_obs_cover_object(video_object),
                                                            cover_path)
        if upload_cover_res.get('status') != 200:
            logger.error('[ObsUploadAdapterImpl/upload] {}/{}: fail to upload cover to OBS, the reason is {}'.
                         format(self.meeting["community"], self.meeting["mid"], upload_cover_res))
            return
        if not isinstance(upload_cover_res, dict) or 'status' not in upload_cover_res.keys():
            logger.error('[ObsUploadAdapterImpl/upload] {}/{} Unexpected upload cover result to OBS: {}'.
                         format(self.meeting["community"], self.meeting["mid"], upload_video_res))
            return
        return video_object
