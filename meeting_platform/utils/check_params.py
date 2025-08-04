# -*- coding: utf-8 -*-
# @Time    : 2023/10/25 11:12
# @Author  : Tom_zc
# @FileName: check_params.py
# @Software: PyCharm
import datetime
import re
import copy
import logging

from html.parser import HTMLParser

from meeting_platform.utils.ret_api import MyValidationError
from meeting_platform.utils.ret_code import RetCode

logger = logging.getLogger('log')

email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]{1,64}@[a-zA-Z0-9.-]{1,255}\.[a-zA-Z]{2,}$')
url_pattern = re.compile(r'https://|http://|www\.')
crlf_pattern = re.compile(r'\r|\n|\r\n')


def match_email(email_str):
    return email_pattern.match(email_str) is not None


def match_crlf(content):
    return crlf_pattern.findall(content)


def match_url(url_str):
    return url_pattern.findall(url_str)


def check_link(url):
    if len(url) > 255:
        logger.error("invalid link length:{}".format(len(url)))
        raise MyValidationError(RetCode.STATUS_PARAMETER_ERROR)
    if not isinstance(url, str):
        logger.error('Invalid link str: {}'.format(url))
        raise MyValidationError(RetCode.STATUS_PARAMETER_ERROR)
    url = url.lower()
    if not url or not url.startswith('https://') or "redirect" in url or not match_url:
        logger.error('Invalid link format: {}'.format(url))
        raise MyValidationError(RetCode.STATUS_PARAMETER_ERROR)


class XSSParser(HTMLParser):
    def __init__(self, *args, **kwargs):
        super(XSSParser, self).__init__(*args, **kwargs)
        self.result = False

    def handle_starttag(self, tag, attrs):
        if attrs or tag:
            self.result = True


class ParserHandler:
    def __init__(self):
        self.parser = XSSParser()

    def __enter__(self): return self.parser

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.parser.close()


def check_invalid_content(content, check_crlf=True):
    # check xss and url, and \r\n
    # 1.check xss
    new_content = copy.deepcopy(content)
    new_content = new_content.strip()
    with ParserHandler() as f:
        f.feed(new_content)
        if f.result:
            logger.error("check xss:{}".format(new_content))
            raise MyValidationError(RetCode.STATUS_START_VALID_XSS)
    # 2.check url
    reg = match_url(content)
    if reg:
        logger.error("check invalid url:{}".format(",".join(reg)))
        raise MyValidationError(RetCode.STATUS_START_VALID_URL)
    # 3.check \r\n
    if check_crlf:
        reg = match_crlf(content)
        if reg:
            logger.error("check crlf")
            raise MyValidationError(RetCode.STATUS_START_VALID_CRLF)


def check_field(field, field_bit):
    if not field or len(field) == 0 or len(field) > field_bit:
        logger.error("check invalid field({}) over bit({})".format(str(field), str(field_bit)))
        raise MyValidationError(RetCode.STATUS_PARAMETER_ERROR)


def check_date(date_str):
    try:
        return datetime.datetime.strptime(date_str, '%Y-%m-%d')
    except Exception as e:
        logger.error("invalid date:{}, and e:{}".format(date_str, str(e)))
        raise MyValidationError(RetCode.STATUS_PARAMETER_ERROR)


def check_time(time_str):
    """
        time_str is 08:00   08 in 08-11 00 in 00-60 and
        meetings minute is in [0,15,30,45]
    """
    # time_str is 08:00   08 in 08-11 00 in 00-60
    try:
        date_list = time_str.split(":")
        hours_int = int(date_list[0])
        minute_int = int(date_list[1])
    except Exception as e:
        logger.error("e:{}".format(e))
        raise MyValidationError(RetCode.STATUS_PARAMETER_ERROR)
    if hours_int < 8 or hours_int > 22:
        logger.error("hours {} must in 8-22".format(str(hours_int)))
        raise MyValidationError(RetCode.STATUS_PARAMETER_ERROR)
    if minute_int not in [0, 15, 30, 45]:
        logger.error("minute {} must in [0, 15, 30, 45]".format(str(minute_int)))
        raise MyValidationError(RetCode.STATUS_PARAMETER_ERROR)


def check_email_list(email_list_str):
    # len of email list str gt 1000 and the single email limit 50 and limit 20 email
    if len(email_list_str) > 1020:
        logger.error("The length of email_list is gt 1000")
        raise MyValidationError(RetCode.STATUS_MEETING_EMAIL_LIST_OVER_LIMIT)
    email_list = email_list_str.split(";")
    for email in email_list:
        if len(email) > 50:
            logger.error("The length of email is gt 50")
            raise MyValidationError(RetCode.STATUS_MEETING_EMAIL_OVER_LIMIT)
        if email and not match_email(email):
            logger.error("The email does not conform to the format")
            raise MyValidationError(RetCode.STATUS_MEETING_INVALID_EMAIL)


def check_duration(start, end, date, now_time):
    err_msg = list()
    start_time = datetime.datetime.strptime(' '.join([date, start]), '%Y-%m-%d %H:%M')
    end_time = datetime.datetime.strptime(' '.join([date, end]), '%Y-%m-%d %H:%M')
    if start_time <= now_time:
        logger.error('The start time {} should not be later than the current time'.format(str(start)))
        raise MyValidationError(RetCode.STATUS_START_GT_NOW)
    if (start_time - now_time).days >= 60:
        logger.error('The start time {} is at most 60 days later than the current time'.format(str(start)))
        raise MyValidationError(RetCode.STATUS_START_LT_LIMIT)
    if start_time >= end_time:
        logger.error('The start time {} should not be later than the end time {}'.format(str(start), str(end)))
        raise MyValidationError(RetCode.STATUS_START_LT_END)
    return err_msg
