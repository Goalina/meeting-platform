# -*- coding: utf-8 -*-
# @Time    : 2023/10/13 11:47
# @Author  : Tom_zc
# @FileName: common.py
# @Software: PyCharm
import secrets
import shutil
import string
import subprocess
import threading
import time
import uuid
import tempfile
import os
import logging
import traceback

from datetime import datetime
from functools import wraps

logger = logging.getLogger('log')


def start_thread(func, m):
    th = threading.Thread(target=func, args=m)
    th.start()


def get_cur_date():
    cur_date = datetime.now()
    return cur_date


def get_temp_dir():
    return tempfile.gettempdir()


def rm_dir(dir_path):
    if os.path.exists(dir_path):
        return shutil.rmtree(dir_path)


def get_video_path(mid, community):
    tmpdir = get_temp_dir()
    while True:
        uuid_str = str(uuid.uuid4())
        new_uuid_str = uuid_str.replace("-", "")
        dir_name = os.path.join(tmpdir, community, new_uuid_str)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            break
        time.sleep(1)
    target_name = mid + '.mp4'
    target_filename = os.path.join(dir_name, target_name)
    return target_filename


def make_nonce():
    return ''.join(secrets.choice(string.digits) for _ in range(6))


def execute_cmd3(cmd, timeout=30, err_log=False):
    """execute cmd3"""
    try:
        p = subprocess.Popen(cmd.split(), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        t_wait_seconds = 0
        while True:
            if p.poll() is not None:
                break
            if timeout >= 0 and t_wait_seconds >= (timeout * 100):
                p.terminate()
                return -1, "", "execute_cmd3 exceeded time {} seconds in executing".format(timeout)
            time.sleep(0.01)
            t_wait_seconds += 1
        out, err = p.communicate()
        ret = p.returncode
        if ret != 0 and err_log:
            logger.error("execute_cmd3 return {}, std output: {}, err output: {}.".format(ret, out, err))
        return ret, out, err
    except Exception as e:
        return -1, "", "execute_cmd3 exceeded raise, e={}, trace={}".format(str(e), traceback.format_exc())


def func_retry(tries=3, delay=2):
    def deco_retry(fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            for i in range(tries):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    logger.error("func_retry e:{}, traceback:{}".format(e, traceback.format_exc()))
                    time.sleep(delay)
            else:
                raise Exception("fun:{} Retries reached".format(fn.__name__))

        return inner

    return deco_retry


def mask_email_full(email):
    """Desensitization email"""
    try:
        username, domain = email.split('@')
        masked_username = username[:1] + '*' * (len(username) - 1)
        domain_name, domain_suffix = domain.split('.', 1)
        masked_domain = domain_name[:1] + '*' * (len(domain_name) - 1)
        return f"{masked_username}@{masked_domain}.{domain_suffix}"
    except ValueError:
        return str()


def to_anonymous_email_list(email_list):
    """to anonymous email"""
    if email_list:
        email_strs = email_list.split(";")
        desensitization_email = [mask_email_full(email) for email in email_strs]
        return ";".join(desensitization_email)
    return email_list
