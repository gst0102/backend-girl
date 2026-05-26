import time
from datetime import datetime

import httpx

from app.config import get_settings

settings = get_settings()

# 内存缓存 access_token
_token_cache = {"token": None, "expires_at": 0}


async def get_wx_openid(code: str) -> str:
    """调用微信接口，用 code 换取 openid"""
    print(f"get_wx_openid 收到 code: {code}")
    if code == "mock_code":
        print("返回 mock openid")
        return "mock_openid_fixed"
    if not settings.WECHAT_APP_ID or not settings.WECHAT_APP_SECRET:
        raise ValueError("微信小程序 AppID/AppSecret 未配置")

    params = {
        "appid": settings.WECHAT_APP_ID,
        "secret": settings.WECHAT_APP_SECRET,
        "js_code": code,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(settings.WECHAT_LOGIN_URL, params=params)
        data = resp.json()

        if "errcode" in data and data["errcode"] != 0:
            raise ValueError(f"微信登录失败: {data.get('errmsg', '未知错误')}")

        openid = data.get("openid")
        if not openid:
            raise ValueError("微信登录失败: 未获取到 openid")

        return openid


async def get_access_token() -> str:
    """获取微信 access_token（自动缓存，过期自动续期）"""
    global _token_cache

    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires_at"] - 300:
        return _token_cache["token"]

    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={settings.WECHAT_APP_ID}&secret={settings.WECHAT_APP_SECRET}"

    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        data = resp.json()

        if "errcode" in data and data["errcode"] != 0:
            raise ValueError(f"获取 access_token 失败: {data.get('errmsg', '未知错误')}")

        token = data["access_token"]
        _token_cache["token"] = token
        _token_cache["expires_at"] = now + data["expires_in"]

        print(f"access_token 已刷新，有效期 {data['expires_in']} 秒")
        return token


async def send_subscribe_message(
    openid: str,
    template_id: str,
    data: dict,
    page: str = "pages/index/index",
) -> bool:
    """发送微信小程序订阅消息"""
    try:
        access_token = await get_access_token()
    except ValueError as e:
        print(f"[推送失败] 获取 access_token 失败: {e}")
        return False

    url = f"https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={access_token}"

    body = {
        "touser": openid,
        "template_id": template_id,
        "page": page,
        "data": data,
        "miniprogram_state": "trial",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=body)
        result = resp.json()

        errcode = result.get("errcode", -1)
        if errcode == 0:
            print(f"[推送成功] 已发送订阅消息给 {openid}")
            return True
        elif errcode == 43101:
            print(f"[推送失败] 用户拒绝授权订阅消息: {openid}")
            return False
        elif errcode == 40001:
            print(f"[推送失败] access_token 失效，清除缓存重试")
            _token_cache["token"] = None
            _token_cache["expires_at"] = 0
            return False
        else:
            print(f"[推送失败] 微信API返回错误: errcode={errcode}, errmsg={result.get('errmsg', '')}")
            return False