# -*- coding: utf-8 -*-
# @Time    : 2024/6/17 18:49
# @Author  : Tom_zc
# @FileName: email_client.py
# @Software: PyCharm
import datetime
import icalendar
import pytz
import copy
import logging

from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings

from meeting.domain.repository.message_adapter import MessageAdapter
from meeting_platform.utils.client.email_client import EmailClient
from meeting_platform.utils.common import func_retry
from meeting_platform.utils.file_stream import read_content

logger = logging.getLogger("log")


class EmailAdapter:
    """email Adapter"""

    def __init__(self, community):
        self.community = community
        smtp_info = settings.COMMUNITY_SMTP.get(community)
        if smtp_info is None:
            logger.info("get empty smtp config from {}".format(community))
            self.email_adapter = None
        else:
            self.smtp_message_from = smtp_info["SMTP_MESSAGE_FROM"]
            if not smtp_info.get("SMTP_SERVER_HOST") or not smtp_info.get("SMTP_SERVER_PORT"):
                logger.info("get empty SMTP_SERVER_HOST or SMTP_SERVER_PORT about smtp config from {}".
                            format(community))
                self.email_adapter = None
                return
            self.email_adapter = EmailClient(smtp_info["SMTP_SERVER_HOST"], smtp_info["SMTP_SERVER_PORT"],
                                             smtp_info["SMTP_SERVER_USER"], smtp_info["SMTP_SERVER_PASS"])

    def send_message(self, receive_str, msg):
        if self.email_adapter:
            msg['From'] = '{} conference <{}>'.format(self.community, self.smtp_message_from)
            return self.email_adapter.send_message(self.smtp_message_from, receive_str, msg)


class EmailTemplate:
    """Email Template"""

    def __init__(self, meeting):
        """meeting must be dict"""
        print(meeting)
        self.email_list = meeting["email_list"]
        if self.email_list:
            toaddrs = self.email_list.replace(' ', '').replace('，', ',').replace(';', ',').replace('；', ',')
            self.toaddrs_list = sorted(list(set(filter(lambda x: x, toaddrs.split(',')))))
        else:
            self.toaddrs_list = list()
        self.topic = meeting["topic"]
        self.etherpad = meeting["etherpad"] or ""
        self.join_url = meeting["join_url"]
        self.sig_name = meeting["group_name"]
        self.agenda = meeting["agenda"]
        self.record = meeting["is_record"]
        self.platform = meeting["platform"].replace('TENCENT', 'Tencent'). \
            replace('WELINK', 'WeLink').replace("ZOOM", 'Zoom')
        self.date = meeting.get("date")
        self.start = meeting.get("start")
        self.end = meeting.get("end")
        portal_info = settings.COMMUNITY_PORTAL[meeting["community"]]
        self.portal_zh = portal_info["PORTAL_ZH"]
        self.portal_en = portal_info["PORTAL_EN"]
        self.community = meeting["community"]
        self.mid = meeting["mid"]
        self.sequence = meeting.get("sequence") or 0
        self.sub_info = meeting.get("sub_info")
        self.start_date = meeting.get("start_date")
        self.end_date = meeting.get("end_date")
        self.cycle_start = meeting.get("cycle_start")
        self.cycle_end = meeting.get("cycle_end")
        self.cycle_type = meeting.get("cycle_type")
        self.cycle_interval = meeting.get("cycle_interval")
        self.cycle_point = meeting.get("cycle_point")
        self.is_cycle = meeting.get("is_cycle")
        if not self.is_cycle:
            self.start_time = ' '.join([self.date, self.start])
        else:
            self.start_time = '{}-{} {} {}'.format(self.start_date, self.end_date, self.cycle_start, self.cycle_end)
        self.action = meeting.get("action")

    # noinspection DuplicatedCode
    def get_create_meeting_template_by_meetings_info(self):
        if not self.agenda and not self.record:
            body = read_content(settings.TEMPLATE.get("TEMPLATE_NOT_SUMMARY_NOT_RECORDING"))
        elif self.agenda and not self.record:
            body = read_content(settings.TEMPLATE.get("TEMPLATE_SUMMARY_NOT_RECORDING"))
        elif not self.agenda and self.record:
            body = read_content(settings.TEMPLATE.get("TEMPLATE_NOT_SUMMARY_RECORDING"))
        elif self.agenda and self.record:
            body = read_content(settings.TEMPLATE.get("TEMPLATE_SUMMARY_RECORDING"))
        else:
            raise Exception("invalid {}/{}".format(self.agenda, self.record))
        body_of_email = body.replace('{{sig_name}}', self.sig_name).replace('{{start_time}}', self.start_time). \
            replace('{{join_url}}', self.join_url).replace('{{topic}}', self.topic). \
            replace('{{etherpad}}', self.etherpad).replace('{{platform}}', self.platform). \
            replace('{{portal_zh}}', self.portal_zh).replace('{{portal_en}}', self.portal_en). \
            replace('{{summary}}', str(self.agenda))
        return MIMEText(body_of_email, _charset='utf-8')

    def get_delete_meeting_template_by_meeting_info(self):
        body = read_content(settings.TEMPLATE.get("TEMPLATE_CANCEL_EMAIL"))
        body_of_email = body.replace('{{platform}}', self.platform). \
            replace('{{start_time}}', self.start_time). \
            replace('{{sig_name}}', self.sig_name)
        return MIMEText(body_of_email, _charset='utf-8')

    def __get_before_start_and_end(self):
        if not self.is_cycle:
            meeting_date = self.date
            meeting_start = self.start
            meeting_end = self.end
        else:
            sub_info = sorted(self.sub_info, key=lambda x: x["date"])
            meeting_date = sub_info[0]["date"]
            meeting_start = sub_info[0]["start"]
            meeting_end = sub_info[0]["end"]
        before_start = datetime.datetime.strptime(
            meeting_date + ' ' + meeting_start, '%Y-%m-%d %H:%M') - datetime.timedelta(hours=8)
        before_end = datetime.datetime.strptime(
            meeting_date + ' ' + meeting_end, '%Y-%m-%d %H:%M') - datetime.timedelta(hours=8)
        dt_start = before_start.replace(tzinfo=pytz.utc)
        dt_end = before_end.replace(tzinfo=pytz.utc)
        return dt_start, dt_end

    def __get_add_icalendar_event(self):
        dt_start, dt_end = self.__get_before_start_and_end()
        event = icalendar.Event()
        event.add('attendee', ','.join(self.toaddrs_list))
        event.add('summary', self.topic)
        event.add('dtstart', dt_start)
        event.add('dtend', dt_end)
        event.add('dtstamp', dt_start)
        event.add('uid', self.platform + str(self.mid))
        event.add('sequence', self.sequence)
        if self.is_cycle:
            r_date_list = list()
            if self.action in ["update_sub_meeting", "delete_sub_meeting"]:
                event.add('recurrence-id', dt_start)
            else:
                for meeting in self.sub_info:
                    if meeting["date"] != dt_start:
                        r_date_list.append(
                            datetime.datetime.strptime(meeting['date'] + ' ' + meeting['start'], '%Y-%m-%d %H:%M')
                            - datetime.timedelta(hours=8)
                        )
                if r_date_list:
                    event.add("rdate", r_date_list)
        return event

    def __get_update_sub_icalendar_event(self):
        before_start = datetime.datetime.strptime(
            self.date + ' ' + self.start, '%Y-%m-%d %H:%M') - datetime.timedelta(hours=8)
        before_end = datetime.datetime.strptime(
            self.date + ' ' + self.end, '%Y-%m-%d %H:%M') - datetime.timedelta(hours=8)
        dt_start = before_start.replace(tzinfo=pytz.utc)
        dt_end = before_end.replace(tzinfo=pytz.utc)
        event = icalendar.Event()
        event.add('attendee', ','.join(self.toaddrs_list))
        event.add('summary', self.topic)
        event.add('dtstart', dt_start)
        event.add('dtend', dt_end)
        event.add('dtstamp', dt_start)
        event.add('uid', self.platform + str(self.mid))
        event.add('sequence', self.sequence)
        event.add('recurrence-id', dt_start)
        return event

    def __get_delete_icalendar_event(self):
        event = icalendar.Event()
        event.add('attendee', ','.join(self.toaddrs_list))
        event.add('summary', self.topic)
        event.add('uid', self.platform + str(self.mid))
        event.add('sequence', self.sequence)
        return event

    def __get_sub_delete_icalendar_event(self):
        before_start = datetime.datetime.strptime(
            self.date + ' ' + self.start, '%Y-%m-%d %H:%M') - datetime.timedelta(hours=8)
        before_end = datetime.datetime.strptime(
            self.date + ' ' + self.end, '%Y-%m-%d %H:%M') - datetime.timedelta(hours=8)
        dt_start = before_start.replace(tzinfo=pytz.utc)
        dt_end = before_end.replace(tzinfo=pytz.utc)
        event = icalendar.Event()
        event.add('attendee', ','.join(self.toaddrs_list))
        event.add('summary', self.topic)
        event.add('dtstart', dt_start)
        event.add('dtend', dt_end)
        event.add('dtstamp', dt_start)
        event.add('uid', self.platform + str(self.mid))
        event.add('sequence', self.sequence)
        event.add('recurrence-id', dt_start)
        return event

    # noinspection DuplicatedCode
    def add_calendar_by_meeting_info(self):
        cal = icalendar.Calendar()
        cal.add('prodid', '-//{} conference calendar'.format(self.community))
        cal.add('version', '2.0')
        cal.add('method', 'REQUEST')
        event = self.__get_add_icalendar_event()
        alarm = icalendar.Alarm()
        alarm.add('action', 'DISPLAY')
        alarm.add('description', 'Reminder')
        alarm.add('TRIGGER;RELATED=START', '-PT15M')
        event.add_component(alarm)
        cal.add_component(event)
        filename = 'invite.ics'
        part = MIMEBase('text', 'calendar', method='REQUEST', name=filename)
        part.set_payload(cal.to_ical())
        encoders.encode_base64(part)
        part.add_header('Content-Description', filename)
        part.add_header('Content-class', 'urn:content-classes:calendarmessage')
        part.add_header('Filename', filename)
        part.add_header('Path', filename)
        return part

    def update_sub_calender_by_meeting_info(self):
        cal = icalendar.Calendar()
        cal.add('prodid', '-//{} conference calendar'.format(self.community))
        cal.add('version', '2.0')
        cal.add('method', 'REQUEST')
        event = self.__get_update_sub_icalendar_event()
        alarm = icalendar.Alarm()
        alarm.add('action', 'DISPLAY')
        alarm.add('description', 'Reminder')
        alarm.add('TRIGGER;RELATED=START', '-PT15M')
        event.add_component(alarm)
        cal.add_component(event)
        filename = 'invite.ics'
        part = MIMEBase('text', 'calendar', method='REQUEST', name=filename)
        part.set_payload(cal.to_ical())
        encoders.encode_base64(part)
        part.add_header('Content-Description', filename)
        part.add_header('Content-class', 'urn:content-classes:calendarmessage')
        part.add_header('Filename', filename)
        part.add_header('Path', filename)
        return part

    def remove_calender_by_meeting_info(self):
        cal = icalendar.Calendar()
        cal.add('prodid', '-//{} conference calendar'.format(self.community))
        cal.add('version', '2.0')
        cal.add('method', 'CANCEL')
        event = self.__get_delete_icalendar_event()
        event.add('sequence', self.sequence)
        cal.add_component(event)
        part = MIMEBase('text', 'calendar', method='CANCEL')
        part.set_payload(cal.to_ical())
        encoders.encode_base64(part)
        part.add_header('Content-class', 'urn:content-classes:calendarmessage')
        return part

    def remove_sub_calender_by_meeting_info(self):
        cal = icalendar.Calendar()
        cal.add('prodid', '-//{} conference calendar'.format(self.community))
        cal.add('version', '2.0')
        cal.add('method', 'CANCEL')
        event = self.__get_sub_delete_icalendar_event()
        event.add('sequence', self.sequence)
        cal.add_component(event)
        part = MIMEBase('text', 'calendar', method='CANCEL')
        part.set_payload(cal.to_ical())
        encoders.encode_base64(part)
        part.add_header('Content-class', 'urn:content-classes:calendarmessage')
        return part


class CreateMessageEmailAdapterImpl(MessageAdapter):
    @func_retry()
    def send_message(self, meeting):
        email_template = EmailTemplate(meeting)
        if not email_template.toaddrs_list:
            logger.info('[CreateMessageEmailAdapterImpl/send_message] no email list to send: {}/{}/{}/{}/{}'.format(
                meeting["community"], meeting["platform"], meeting["topic"], meeting["mid"], meeting["id"]))
            return
        # 构造邮件
        msg = MIMEMultipart()
        # 添加邮件主体
        content = email_template.get_create_meeting_template_by_meetings_info()
        msg.attach(content)
        # 添加日历
        part = email_template.add_calendar_by_meeting_info()
        msg.attach(part)
        # 完善邮件信息
        msg['Subject'] = meeting["topic"]
        msg['To'] = ','.join(email_template.toaddrs_list)
        email_adapter = EmailAdapter(meeting["community"])
        email_adapter.send_message(email_template.toaddrs_list, msg)
        logger.info('[CreateMessageAdapterImpl/send_message] send create meeting email success: {}/{}/{}/{}/{}'.format(
            meeting["community"], meeting["platform"], meeting["topic"], meeting["mid"], meeting["id"]))


class UpdateMessageEmailAdapterImpl(MessageAdapter):
    @func_retry()
    def send_message(self, meeting):
        email_meeting = copy.deepcopy(meeting)
        email_meeting["topic"] = '[Update] ' + email_meeting["topic"]
        email_template = EmailTemplate(email_meeting)
        if not email_template.toaddrs_list:
            logger.info('[UpdateMessageEmailAdapterImpl/send_message] no email list to send: {}/{}/{}/{}/{}'.format(
                email_meeting["community"], email_meeting["platform"], email_meeting["topic"], email_meeting["mid"],
                email_meeting["id"]))
            return
        # 构造邮件
        msg = MIMEMultipart()
        # 添加邮件主体
        content = email_template.get_create_meeting_template_by_meetings_info()
        msg.attach(content)
        # 添加日历
        part = email_template.add_calendar_by_meeting_info()
        msg.attach(part)
        # 完善邮件信息
        msg['Subject'] = email_meeting["topic"]
        msg['To'] = ','.join(email_template.toaddrs_list)
        email_adapter = EmailAdapter(email_meeting["community"])
        email_adapter.send_message(email_template.toaddrs_list, msg)
        logger.info('[UpdateMessageEmailAdapterImpl/send_message] send update meeting email success: {}/{}/{}/{}/{}'.
                    format(email_meeting["community"], email_meeting["platform"], email_meeting["topic"],
                           email_meeting["mid"], email_meeting["id"]))


class UpdateSubMessageEmailAdapterImpl(MessageAdapter):
    @func_retry()
    def send_message(self, meeting):
        email_meeting = copy.deepcopy(meeting)
        email_meeting["topic"] = '[Update] ' + email_meeting["topic"]
        email_template = EmailTemplate(email_meeting)
        if not email_template.toaddrs_list:
            logger.info('[UpdateSubMessageEmailAdapterImpl/send_message] no email list to send: {}/{}/{}/{}/{}'.format(
                email_meeting["community"], email_meeting["platform"], email_meeting["topic"], email_meeting["mid"],
                email_meeting["id"]))
            return
        # 构造邮件
        msg = MIMEMultipart()
        # 添加邮件主体
        content = email_template.get_create_meeting_template_by_meetings_info()
        msg.attach(content)
        # 添加日历
        part = email_template.update_sub_calender_by_meeting_info()
        msg.attach(part)
        # 完善邮件信息
        msg['Subject'] = email_meeting["topic"]
        msg['To'] = ','.join(email_template.toaddrs_list)
        email_adapter = EmailAdapter(email_meeting["community"])
        email_adapter.send_message(email_template.toaddrs_list, msg)
        logger.info('[UpdateSubMessageEmailAdapterImpl/send_message] send update meeting email success: {}/{}/{}/{}/{}'.
                    format(email_meeting["community"], email_meeting["platform"], email_meeting["topic"],
                           email_meeting["mid"], email_meeting["id"]))


class DeleteMessageEmailAdapterImpl(MessageAdapter):
    @func_retry()
    def send_message(self, meeting):
        email_meeting = copy.deepcopy(meeting)
        email_meeting["topic"] = '[Cancel] ' + email_meeting["topic"]
        email_template = EmailTemplate(email_meeting)
        if not email_template.toaddrs_list:
            logger.info('[DeleteMessageEmailAdapterImpl/send_message] no email list to send: {}/{}/{}/{}/{}'.format(
                email_meeting["community"], email_meeting["platform"], email_meeting["topic"], email_meeting["mid"],
                email_meeting["id"]))
            return
        # 构造邮件
        msg = MIMEMultipart()
        # 添加邮件主体
        content = email_template.get_delete_meeting_template_by_meeting_info()
        msg.attach(content)
        # 取消日历
        part = email_template.remove_calender_by_meeting_info()
        msg.attach(part)
        # 完善邮件信息
        msg['Subject'] = email_meeting["topic"]
        msg['To'] = ",".join(email_template.toaddrs_list)
        email_adapter = EmailAdapter(email_meeting["community"])
        email_adapter.send_message(email_template.toaddrs_list, msg)
        logger.info('[DeleteMessageAdapterImpl/send_message] send cancel email success: {}/{}/{}/{}/{}'.format(
            email_meeting["community"], email_meeting["platform"], email_meeting["topic"], email_meeting["mid"],
            email_meeting["id"]))


class DeleteSubMessageEmailAdapterImpl(MessageAdapter):
    @func_retry()
    def send_message(self, meeting):
        email_meeting = copy.deepcopy(meeting)
        email_meeting["topic"] = '[Cancel] ' + email_meeting["topic"]
        email_template = EmailTemplate(email_meeting)
        if not email_template.toaddrs_list:
            logger.info('[DeleteSubMessageEmailAdapterImpl/send_message] no email list to send: {}/{}/{}/{}/{}'.format(
                email_meeting["community"], email_meeting["platform"], email_meeting["topic"], email_meeting["mid"],
                email_meeting["id"]))
            return
        # 构造邮件
        msg = MIMEMultipart()
        # 添加邮件主体
        content = email_template.get_delete_meeting_template_by_meeting_info()
        msg.attach(content)
        # 取消日历
        part = email_template.remove_sub_calender_by_meeting_info()
        msg.attach(part)
        # 完善邮件信息
        msg['Subject'] = email_meeting["topic"]
        msg['To'] = ",".join(email_template.toaddrs_list)
        email_adapter = EmailAdapter(email_meeting["community"])
        email_adapter.send_message(email_template.toaddrs_list, msg)
        logger.info('[DeleteSubMessageEmailAdapterImpl/send_message] send cancel email success: {}/{}/{}/{}/{}'.format(
            email_meeting["community"], email_meeting["platform"], email_meeting["topic"], email_meeting["mid"],
            email_meeting["id"]))
