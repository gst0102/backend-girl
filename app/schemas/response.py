from enum import IntEnum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class CodeEnum(IntEnum):
    SUCCESS = 0
    PARAM_ERROR = 40001
    USER_NOT_FOUND = 40002
    RECORD_EXISTS = 40003
    FEATURE_LOCKED = 40004
    ALREADY_INVITED = 40005
    SELF_INVITE = 40006
    GUARDIAN_EXISTS = 40007
    COUPLE_EXISTS = 40008
    ANIME_NOT_FOUND = 40009
    ALREADY_SUBSCRIBED = 40010
    AUTH_FAILED = 40101
    FORBIDDEN = 40301
    NOT_FOUND = 40401
    RATE_LIMITED = 42901
    SERVER_ERROR = 50001


CODE_MESSAGE: dict[CodeEnum, str] = {
    CodeEnum.SUCCESS: "success",
    CodeEnum.PARAM_ERROR: "参数错误",
    CodeEnum.USER_NOT_FOUND: "用户不存在",
    CodeEnum.RECORD_EXISTS: "今日该类型已记录",
    CodeEnum.FEATURE_LOCKED: "该功能尚未解锁",
    CodeEnum.ALREADY_INVITED: "该用户已被邀请过",
    CodeEnum.SELF_INVITE: "不能邀请自己",
    CodeEnum.GUARDIAN_EXISTS: "已存在有效的守护关系",
    CodeEnum.COUPLE_EXISTS: "任一方已有情侣关系",
    CodeEnum.ANIME_NOT_FOUND: "番剧不存在",
    CodeEnum.ALREADY_SUBSCRIBED: "已订阅该番剧",
    CodeEnum.AUTH_FAILED: "认证失败，Token 无效或已过期",
    CodeEnum.FORBIDDEN: "无权限访问",
    CodeEnum.NOT_FOUND: "资源不存在",
    CodeEnum.RATE_LIMITED: "请求过于频繁",
    CodeEnum.SERVER_ERROR: "服务器内部错误",
}


class ResponseModel(BaseModel, Generic[T]):
    code: int = CodeEnum.SUCCESS.value
    message: str = CODE_MESSAGE[CodeEnum.SUCCESS]
    data: T | None = None


class ErrorResponse(BaseModel):
    code: int
    message: str
    data: None = None


def success_response(data: Any = None, message: str | None = None) -> ResponseModel:
    return ResponseModel(
        code=CodeEnum.SUCCESS.value,
        message=message or CODE_MESSAGE[CodeEnum.SUCCESS],
        data=data,
    )


def error_response(code: CodeEnum, detail: str | None = None) -> ErrorResponse:
    msg = CODE_MESSAGE.get(code, "未知错误")
    if detail:
        msg = f"{msg}: {detail}"
    return ErrorResponse(
        code=code.value,
        message=msg,
        data=None,
    )


def error_json(code: CodeEnum, detail: str | None = None):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=200,
        content=error_response(code, detail).model_dump(),
    )