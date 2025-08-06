# -*- coding: utf-8 -*-
# @Time    : 2023/10/11 16:09
# @Author  : Tom_zc
# @FileName: operation_log.py
# @Software: PyCharm
import json
from logging import getLogger
from functools import wraps

from rest_framework.response import Response
from django.http import JsonResponse
from django.conf import settings

logger = getLogger("django")

logger_template = "(Client ip:{}, User id:{}, Module:{},Type:{}) Detail:{}--->Result:{}."

log_key = "log_vars"


def is_en(): return settings.LANGUAGE_CODE == 'en-us'


class OperationBase:
    EN_OPERATION = dict()
    CN_OPERATION = dict()

    @classmethod
    def get_name_by_code(cls, code):
        if is_en():
            return cls.EN_OPERATION.get(code)
        else:
            return cls.CN_OPERATION.get(code)

    @classmethod
    def get_code_by_name(cls, name):
        if is_en():
            temp = {value: key for key, value in cls.EN_OPERATION.items()}
            return temp.get(name, str())
        else:
            temp = {value: key for key, value in cls.CN_OPERATION.items()}
            return temp.get(name, str())


class OperationLogModule(OperationBase):
    OP_MODULE_MEETING = 0

    CN_OPERATION = {
        OP_MODULE_MEETING: "会议",
    }

    EN_OPERATION = {
        OP_MODULE_MEETING: "meeting",
    }


class OperationLogType(OperationBase):
    OP_TYPE_LOGIN = 0
    OP_TYPE_LOGOUT = 1
    OP_TYPE_CREATE = 2
    OP_TYPE_DELETE = 3
    OP_TYPE_QUERY = 4
    OP_TYPE_MODIFY = 5
    OP_TYPE_EXPORT = 6
    OP_TYPE_DOWNLOAD = 7
    OP_TYPE_LOGOFF = 8
    OP_TYPE_COLLECT = 9
    OP_TYPE_CANCEL_COLLECT = 10
    OP_TYPE_REFRESH = 11

    CN_OPERATION = {
        OP_TYPE_LOGIN: "登录",
        OP_TYPE_LOGOUT: "登出",
        OP_TYPE_LOGOFF: "注销",
        OP_TYPE_CREATE: "新建",
        OP_TYPE_DELETE: "删除",
        OP_TYPE_QUERY: "查询",
        OP_TYPE_MODIFY: "修改",
        OP_TYPE_EXPORT: "导出",
        OP_TYPE_DOWNLOAD: "下载",
        OP_TYPE_COLLECT: "收藏",
        OP_TYPE_CANCEL_COLLECT: "取消收藏",
        OP_TYPE_REFRESH: "刷新",
    }

    EN_OPERATION = {
        OP_TYPE_LOGIN: "login",
        OP_TYPE_LOGOUT: "logout",
        OP_TYPE_LOGOFF: "logoff",
        OP_TYPE_CREATE: "create",
        OP_TYPE_DELETE: "delete",
        OP_TYPE_QUERY: "query",
        OP_TYPE_MODIFY: "modify",
        OP_TYPE_EXPORT: "export",
        OP_TYPE_DOWNLOAD: "download",
        OP_TYPE_COLLECT: "collect",
        OP_TYPE_CANCEL_COLLECT: "cancel collect",
        OP_TYPE_REFRESH: "refresh",
    }


class OperationLogResult(OperationBase):
    OP_RESULT_SUCCEED = 0
    OP_RESULT_FAILED = 1

    CN_OPERATION = {
        OP_RESULT_SUCCEED: "成功",
        OP_RESULT_FAILED: "失败",
    }

    EN_OPERATION = {
        OP_RESULT_SUCCEED: "succeed",
        OP_RESULT_FAILED: "failed"
    }


class OperationLogDesc(OperationBase):
    # USER CODE START 0
    # MEETING CODE START 1000

    OP_DESC_MEETING_BASE_CODE = 1000
    OP_DESC_MEETING_CREATE_CODE = OP_DESC_MEETING_BASE_CODE + 1
    OP_DESC_MEETING_UPDATE_CODE = OP_DESC_MEETING_BASE_CODE + 2
    OP_DESC_MEETING_DELETE_CODE = OP_DESC_MEETING_BASE_CODE + 3
    OP_DESC_MEETING_TRANSLATE_CALLBACK_CODE = OP_DESC_MEETING_BASE_CODE + 4
    OP_DESC_MEETING_UPDATE_SUB_CODE = OP_DESC_MEETING_BASE_CODE + 5
    OP_DESC_MEETING_DELETE_SUB_CODE = OP_DESC_MEETING_BASE_CODE + 6

    CN_OPERATION = {
        # meeting
        OP_DESC_MEETING_CREATE_CODE: "创建会议（%s/%s/%s）。",
        OP_DESC_MEETING_UPDATE_CODE: "修改会议（%s/%s/%s）。",
        OP_DESC_MEETING_DELETE_CODE: "删除会议（%s/%s/%s）。",
        OP_DESC_MEETING_TRANSLATE_CALLBACK_CODE: "翻译会议（%s）。",
        OP_DESC_MEETING_UPDATE_SUB_CODE: "修改子会议（%s/%s）。",
        OP_DESC_MEETING_DELETE_SUB_CODE: "删除子会议（%s）。",
    }

    EN_OPERATION = {
        # meeting
        OP_DESC_MEETING_CREATE_CODE: "Create meeting(%s/%s/%s).",
        OP_DESC_MEETING_UPDATE_CODE: "Update meeting(%s/%s/%s).",
        OP_DESC_MEETING_DELETE_CODE: "Delete meeting(%s/%s/%s).",
        OP_DESC_MEETING_TRANSLATE_CALLBACK_CODE: "Translate meeting(%s).",
        OP_DESC_MEETING_UPDATE_SUB_CODE: "Update sub meeting(%s/%s).",
        OP_DESC_MEETING_DELETE_SUB_CODE: "Delete sub meeting(%s).",

    }


def console_log(request, log_module, log_desc, log_type, log_vars, resp=None):
    ip = "unknown"
    user_id = "anonymous"
    if request.user and request.user.id:
        user_id = request.user.id
        ip = request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR")
    result = OperationLogResult.OP_RESULT_FAILED
    if isinstance(resp, Response) and str(resp.status_code).startswith("20"):
        result = OperationLogResult.OP_RESULT_SUCCEED
    elif isinstance(resp, JsonResponse):
        json_data = json.loads(resp.content)
        if str(json_data.get("code")).startswith("20"):
            result = OperationLogResult.OP_RESULT_SUCCEED
    elif resp:
        result = OperationLogResult.OP_RESULT_SUCCEED
    log_module_str = OperationLogModule.get_name_by_code(log_module)
    log_type_str = OperationLogType.get_name_by_code(log_type)
    log_desc_str = OperationLogDesc.get_name_by_code(log_desc)
    log_result_str = OperationLogResult.get_name_by_code(result)
    log_vars_tuple = tuple() if log_vars is None else tuple(log_vars)
    log_detail = log_desc_str % log_vars_tuple
    msg = logger_template.format(ip, user_id, log_module_str, log_type_str, log_detail, log_result_str)
    logger.info(msg)


class LoggerContext:
    def __init__(self, request, log_module, log_type, log_desc):
        self.request = request
        self.log_module = log_module
        self.log_type = log_type
        self.log_desc = log_desc
        self.log_vars = list()
        self.result = None

    def __enter__(self): return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        console_log(self.request, self.log_module, self.log_desc, self.log_type, self.log_vars, self.result)


def set_log_thread_local(request, key, value):
    setattr(request, key, value)


def get_log_thread_local(request, key):
    if hasattr(request, key):
        return getattr(request, key)
    return None


def logger_wrapper(log_module, log_type, log_desc):
    def wrapper(fn):
        @wraps(fn)
        def inner(view, request, *args, **kwargs):
            with LoggerContext(request, log_module, log_type, log_desc) as log_context:
                log_context.log_vars = ["anonymous"]
                try:
                    resp = fn(view, request, *args, **kwargs)
                    log_context.result = resp
                    return resp
                finally:
                    log_context.request.user = request.user
                    log_vars = get_log_thread_local(request, log_key)
                    if log_vars:
                        log_context.log_vars = log_vars
                    else:
                        log_context.log_vars = [request.user.id]

        return inner

    return wrapper
