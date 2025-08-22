# -*- coding: utf-8 -*-
# @Time    : 2023/10/26 18:52
# @Author  : Tom_zc
# @FileName: ret_code.py
# @Software: PyCharm


class RetCodeBase:
    EN_OPERATION = dict()
    CN_OPERATION = dict()

    @classmethod
    def get_name_by_code(cls, code, is_en=False):
        if is_en:
            return cls.EN_OPERATION.get(code)
        else:
            return cls.CN_OPERATION.get(code)

    @classmethod
    def get_code_by_name(cls, name, is_en=False):
        if is_en:
            temp = {value: key for key, value in cls.EN_OPERATION.items()}
            return temp.get(name, str())
        else:
            temp = {value: key for key, value in cls.CN_OPERATION.items()}
            return temp.get(name, str())


class RetCode(RetCodeBase):
    # common
    STATUS_SUCCESS = 0
    STATUS_PARAMETER_ERROR = -1
    STATUS_PARTIAL_SUCCESS = -2
    INTERNAL_ERROR = -3
    SYSTEM_BUSY = -4
    NAME_NOT_STANDARD = -5
    RESULT_IS_EMPTY = -6
    STATUS_PARAMETER_CORRESPONDING_ERROR = -7
    STATUS_FAILED = -8
    INFORMATION_CHANGE_ERROR = -9
    STATUS_START_LT_END = -10
    STATUS_START_GT_NOW = -11
    STATUS_START_LT_LIMIT = -12
    STATUS_START_VALID_URL = -13
    STATUS_START_VALID_XSS = -14
    STATUS_START_VALID_CRLF = -15
    STATUS_AUTH_FAILED = -16
    STATUS_INVALID_CONTENT_FAILED = -17

    STATUS_FACILITY_BIT_MASK = 16
    STATUS_FACILITY_MEETING = 1 << STATUS_FACILITY_BIT_MASK

    # sub module: meeting
    STATUS_MEETING_EMAIL_LIST_OVER_LIMIT = STATUS_FACILITY_MEETING + 0
    STATUS_MEETING_EMAIL_OVER_LIMIT = STATUS_FACILITY_MEETING + 1
    STATUS_MEETING_INVALID_EMAIL = STATUS_FACILITY_MEETING + 2
    STATUS_MEETING_INVALID_ETHERPAD = STATUS_FACILITY_MEETING + 3
    STATUS_MEETING_FAILED_CREATE = STATUS_FACILITY_MEETING + 4
    STATUS_MEETING_NO_AVAILABLE_HOST = STATUS_FACILITY_MEETING + 5
    STATUS_MEETING_DATE_CONFLICT = STATUS_FACILITY_MEETING + 6
    STATUS_MEETING_CANNOT_BE_OPERATE = STATUS_FACILITY_MEETING + 7
    STATUS_MEETING_NO_PERMISSION = STATUS_FACILITY_MEETING + 8
    STATUS_MEETING_INVALID_GROUP_NAME = STATUS_FACILITY_MEETING + 9
    STATUS_MEETING_INVALID_START = STATUS_FACILITY_MEETING + 10
    STATUS_MEETING_NOT_EXIST = STATUS_FACILITY_MEETING + 11
    STATUS_MEETING_FAILED_UPDATE = STATUS_FACILITY_MEETING + 12
    STATUS_MEETING_CANNOT_BE_OPERATE_BY_EXPIRED = STATUS_FACILITY_MEETING + 13
    STATUS_MEETING_CREATE_COUNT_LIMIT = STATUS_FACILITY_MEETING + 14
    STATUS_MEETING_MODIFY_COUNT_LIMIT = STATUS_FACILITY_MEETING + 15
    STATUS_MEETING_PUT_RUNNING = STATUS_FACILITY_MEETING + 16
    STATUS_MEETING_REPEAT_FAILED = STATUS_FACILITY_MEETING + 17
    STATUS_MEETING_CANNOT_DELETE_FAILED = STATUS_FACILITY_MEETING + 18
    STATUS_MEETING_IN_HALF_YEAR_FAILED = STATUS_FACILITY_MEETING + 19

    EN_OPERATION = {
        # common
        STATUS_SUCCESS: "Successfully",
        STATUS_PARTIAL_SUCCESS: "Partially successful, data may be incomplete, please check the cluster for exceptions",
        STATUS_PARAMETER_ERROR: "Parameter invalid",
        STATUS_FAILED: "Failed",
        INTERNAL_ERROR: 'Internal Error, Please try again',
        SYSTEM_BUSY: 'The system is busy',
        NAME_NOT_STANDARD: 'name not standard',
        RESULT_IS_EMPTY: 'The result is empty',
        STATUS_PARAMETER_CORRESPONDING_ERROR: 'Parameter corresponding invalid',
        INFORMATION_CHANGE_ERROR: "The information has changed, Please refresh and try again",
        STATUS_START_LT_END: "The start time should not be later than the end time",
        STATUS_START_GT_NOW: "The start time should not be later than the current time",
        STATUS_START_LT_LIMIT: "The start time is at most 60 days later than the current time",
        STATUS_START_VALID_URL: "Please do not enter URL links",
        STATUS_START_VALID_XSS: "Please do not enter XSS tags",
        STATUS_START_VALID_CRLF: "Please do not enter \r\n tags",
        STATUS_AUTH_FAILED: "Auth failed",
        STATUS_INVALID_CONTENT_FAILED: "Check the content you entered. It is not compliant. "
                                       "Please re-enter.",

        # meetings
        STATUS_MEETING_EMAIL_LIST_OVER_LIMIT: "The length of email_list is gt 600",
        STATUS_MEETING_EMAIL_OVER_LIMIT: "The length of email is gt 50",
        STATUS_MEETING_INVALID_EMAIL: "Invalid email address",
        STATUS_MEETING_INVALID_ETHERPAD: "Invalid etherpad",
        STATUS_MEETING_FAILED_CREATE: "Failed to create meeting",
        STATUS_MEETING_FAILED_UPDATE: "Failed to update meeting",
        STATUS_MEETING_NO_AVAILABLE_HOST: "There is currently no available host, please go to the official website to "
                                          "view scheduled meetings",
        STATUS_MEETING_DATE_CONFLICT: "Time conflict, please adjust the time to schedule the meeting",
        STATUS_MEETING_CANNOT_BE_OPERATE: "Cannot be deleted or update 1 hours before the meeting",
        STATUS_MEETING_NO_PERMISSION: "Failed to operate a meeting due to insufficient permissions",
        STATUS_MEETING_INVALID_GROUP_NAME: "Invalid SIG name",
        STATUS_MEETING_INVALID_START: "The start time should not be earlier than the current time",
        STATUS_MEETING_NOT_EXIST: "Meeting does not exist",
        STATUS_MEETING_CANNOT_BE_OPERATE_BY_EXPIRED: "Meeting is expired",
        STATUS_MEETING_CREATE_COUNT_LIMIT: "The meeting created today has exceeded the limit. Please try again tomorrow",
        STATUS_MEETING_MODIFY_COUNT_LIMIT: "Modifying the meeting has exceeded the limit",
        STATUS_MEETING_PUT_RUNNING: "The meeting is in progress and cannot be operated",
        STATUS_MEETING_REPEAT_FAILED: "The meeting is repeated and the operation failed.",
        STATUS_MEETING_CANNOT_DELETE_FAILED: "There is only one sub-meeting left in the recurring meeting,"
                                             "Please delete the entire recurring meeting.",
        STATUS_MEETING_IN_HALF_YEAR_FAILED: "The end date of a recurring meeting can only be within six months, "
                                            "The operation failed.",

    }

    CN_OPERATION = {
        # common
        STATUS_SUCCESS: "操作成功",
        STATUS_PARTIAL_SUCCESS: "部分成功，请求数据可能不完整，请检查",
        STATUS_PARAMETER_ERROR: "参数无效",
        STATUS_FAILED: "操作失败",
        INTERNAL_ERROR: '内部错误，请稍后重试',
        SYSTEM_BUSY: '系统繁忙，请稍后重试',
        NAME_NOT_STANDARD: '非法名字',
        RESULT_IS_EMPTY: '结果为空',
        STATUS_PARAMETER_CORRESPONDING_ERROR: '参数响应无效',
        INFORMATION_CHANGE_ERROR: "信息发生变化，请刷新后重试",
        STATUS_START_LT_END: "会议开始时间应小于结束时间",
        STATUS_START_GT_NOW: "会议开始时间应大于当前时间",
        STATUS_START_LT_LIMIT: "建议预定60天之内的会议",
        STATUS_START_VALID_URL: "请勿输入URL链接，XSS标签等内容",
        STATUS_START_VALID_XSS: "请勿输入XSS标签等内容",
        STATUS_START_VALID_CRLF: "请勿输入\r\n等内容",
        STATUS_AUTH_FAILED: "认证失败",
        STATUS_INVALID_CONTENT_FAILED: "检查你输入的内容不合规，请重新输入",

        # meetings
        STATUS_MEETING_EMAIL_LIST_OVER_LIMIT: "邮件地址长度超限",
        STATUS_MEETING_EMAIL_OVER_LIMIT: "单封邮件地址长度超限",
        STATUS_MEETING_INVALID_EMAIL: "无效的邮件地址",
        STATUS_MEETING_INVALID_ETHERPAD: "无效的Etherpad链接",
        STATUS_MEETING_FAILED_CREATE: "创建会议失败",
        STATUS_MEETING_FAILED_UPDATE: "修改会议失败",
        STATUS_MEETING_NO_AVAILABLE_HOST: "目前没有可用的主持人，请前往官网查看预约会议",
        STATUS_MEETING_DATE_CONFLICT: "会议时间冲突，请调整会议预定时间(距离会议开始或结束半小时内存在会议)",
        STATUS_MEETING_CANNOT_BE_OPERATE: "距离会议开始时间小于一个小时，无法修改或删除",
        STATUS_MEETING_NO_PERMISSION: "权限不足导致操作会议失败",
        STATUS_MEETING_INVALID_GROUP_NAME: "错误的SIG组名",
        STATUS_MEETING_INVALID_START: "请输入正确的开始时间",
        STATUS_MEETING_NOT_EXIST: "会议不存在",
        STATUS_MEETING_CANNOT_BE_OPERATE_BY_EXPIRED: "会议已经过期，操作失败",
        STATUS_MEETING_CREATE_COUNT_LIMIT: "今日创建会议已超限制，请明日再重试",
        STATUS_MEETING_MODIFY_COUNT_LIMIT: "修改会议已超限制",
        STATUS_MEETING_PUT_RUNNING: "会议正在进行中，无法操作此会议",
        STATUS_MEETING_REPEAT_FAILED: "你创建的会议已经存在，请勿重复创建，操作失败",
        STATUS_MEETING_CANNOT_DELETE_FAILED: "周期性会议目前只剩一场子会议，请删除整个周期性会议",
        STATUS_MEETING_IN_HALF_YEAR_FAILED: "周期性会议结束日期只能为半年内，操作失败",

    }
