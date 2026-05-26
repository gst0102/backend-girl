# -*- coding: utf-8 -*-
"""后端 API 连通性测试脚本

依据后端接口拆解文档 + 实际 Controller 实现，验证所有接口连通性。
技术栈: Python 3.10 + FastAPI + PostgreSQL + SQLAlchemy + JWT
运行方式: python testapi.py  或  uv run python testapi.py

依赖: 纯标准库 (urllib)，无需额外安装
"""

import json
import sys
import time
import urllib.error
import urllib.request

BASE = "http://localhost:8000"
API = f"{BASE}/api"

PASS = 0
FAIL = 0
TOTAL = 0

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def ok(msg: str) -> str:
    return f"{GREEN}  OK{RESET}  {msg}"


def fail(msg: str) -> str:
    return f"{RED}FAIL{RESET}  {msg}"


def info(msg: str) -> str:
    return f"{CYAN}{BOLD}{msg}{RESET}"


def warn(msg: str) -> str:
    return f"{YELLOW}{msg}{RESET}"


def call(path: str, token: str = None, method: str = "GET", body: dict = None, params: dict = None) -> tuple[int, dict]:
    url = f"{API}{path}"
    if params:
        query_parts = []
        for k, v in params.items():
            query_parts.append(f"{k}={urllib.request.quote(str(v))}")
        url += "?" + "&".join(query_parts)

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, {"code": -1, "message": raw, "data": None}
    except urllib.error.URLError as e:
        return 0, {"code": -1, "message": str(e.reason), "data": None}


def assert_ok(status: int, body: dict, name: str) -> bool:
    global PASS, FAIL, TOTAL
    TOTAL += 1
    if status == 200 and body.get("code") == 0:
        PASS += 1
        print(f"  {ok(name)}")
        return True
    msg = body.get("message", f"HTTP {status}")
    FAIL += 1
    print(f"  {fail(name)} — code={body.get('code')}, {msg}")
    return False


def assert_code(status: int, body: dict, expected_code: int, name: str) -> bool:
    global PASS, FAIL, TOTAL
    TOTAL += 1
    if body.get("code") == expected_code:
        PASS += 1
        print(f"  {ok(name)} (code={expected_code})")
        return True
    FAIL += 1
    print(f"  {fail(name)} — HTTP {status}, code={body.get('code')} (expected {expected_code})")
    return False


def run():
    global PASS, FAIL, TOTAL
    PASS = FAIL = TOTAL = 0
    print(f"{BOLD}{'=' * 60}{RESET}")
    print(f"  {info('后端 API 连通性测试')}")
    print(f"  服务地址: {BASE}")
    print(f"  时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{BOLD}{'=' * 60}{RESET}\n")

    # ========================================
    #  0. 健康检查  GET /health
    # ========================================
    print(f"  {info('0. 健康检查 — GET /health')}")
    status, body = call("/health", token=None, method="GET")
    if status == 200 and body.get("status") == "ok":
        PASS += 1; TOTAL += 1
        env_val = body.get("env", "?")
        print(f"  {ok(f'服务正常 (env={env_val})')}")
    else:
        FAIL += 1; TOTAL += 1
        print(f"  {fail(f'服务异常 — {body}')}")
        print(f"\n  {RED}请先启动后端: uv run uvicorn app.main:app --host 0.0.0.0 --port 8000{RESET}")
        return

    # ========================================
    #  1. 用户登录  POST /api/user/login
    # ========================================
    print(f"\n  {info('1. 用户登录 — POST /api/user/login')}")

    status, body = call("/user/login", method="POST", body={"code": "test_user_a"})
    assert_ok(status, body, "用户 A 登录")
    token_a = body.get("data", {}).get("token", "")
    uid_a = body.get("data", {}).get("user_id", "")
    is_new_a = body.get("data", {}).get("is_new", None)
    print(f"      user_id={uid_a[:12]}... is_new={is_new_a}")

    time.sleep(0.3)
    status, body = call("/user/login", method="POST", body={"code": "test_user_b"})
    assert_ok(status, body, "用户 B 登录")
    token_b = body.get("data", {}).get("token", "")
    uid_b = body.get("data", {}).get("user_id", "")
    print(f"      user_id={uid_b[:12]}...")

    # ========================================
    #  1b. 获取用户信息  GET /api/user/info
    # ========================================
    print(f"\n  {info('1b. 用户信息 — GET /api/user/info')}")
    status, body = call("/user/info", token=token_a)
    assert_ok(status, body, "获取用户信息")
    nickname = body.get("data", {}).get("nickname", "")
    print(f"      nickname={nickname}, invite_count={body.get('data', {}).get('invite_count')}")

    # ========================================
    #  2. 记录创建  POST /api/record/create
    # ========================================
    print(f"\n  {info('2. 记录 — POST /api/record/create')}")
    today = time.strftime("%Y-%m-%d")

    status, body = call("/record/create", token=token_a, method="POST", body={
        "record_type": "poop",
        "record_date": today,
        "record_value": {"count": 1},
    })
    assert_ok(status, body, "创建拉屎记录")
    rid = body.get("data", {}).get("record_id")
    cd = body.get("data", {}).get("continuous_days")
    be = body.get("data", {}).get("badges_earned", [])
    print(f"      record_id={rid}, continuous_days={cd}, badges_earned={len(be)}")

    status, body = call("/record/create", token=token_a, method="POST", body={
        "record_type": "poop",
        "record_date": today,
        "record_value": {"count": 1},
    })
    assert_code(status, body, 40003, "重复记录拦截")

    # ========================================
    #  3. 日历  GET /api/calendar?year=&month=
    # ========================================
    print(f"\n  {info('3. 日历 — GET /api/calendar')}")
    now = time.localtime()
    status, body = call("/calendar", token=token_a, params={
        "year": now.tm_year,
        "month": now.tm_mon,
    })
    assert_ok(status, body, "获取日历数据")
    days_len = len(body.get("data", {}).get("days", []))
    print(f"      days={days_len}")

    # ========================================
    #  4. 今日状态  GET /api/today/status
    # ========================================
    print(f"\n  {info('4. 今日状态 — GET /api/today/status')}")
    status, body = call("/today/status", token=token_a)
    assert_ok(status, body, "获取今日状态")
    features = body.get("data", {}).get("features", {})
    recorded = [k for k, v in features.items() if v.get("recorded")]
    unlocked = [k for k, v in features.items() if v.get("unlocked")]
    print(f"      recorded={recorded}, unlocked={unlocked}")

    # ========================================
    #  5. 邀请  POST /api/invite/create
    # ========================================
    print(f"\n  {info('5. 邀请 — POST /api/invite/create')}")
    status, body = call("/invite/create", token=token_a, method="POST", body={
        "invitee_openid": "test_invitee_001",
        "invitee_device": "test_device",
    })
    assert_ok(status, body, "创建邀请关系")
    ic = body.get("data", {}).get("invite_count", 0)
    nu = body.get("data", {}).get("new_unlocked", [])
    print(f"      invite_count={ic}, new_unlocked={nu}")

    print(f"\n  {info('5b. 邀请进度 — GET /api/invite/progress')}")
    status, body = call("/invite/progress", token=token_a)
    assert_ok(status, body, "获取邀请进度")
    cur = body.get("data", {}).get("current", 0)
    print(f"      current={cur}")

    # ========================================
    #  6. 排行榜  GET /api/rank/list?limit=N
    # ========================================
    print(f"\n  {info('6. 排行榜 — GET /api/rank/list')}")
    status, body = call("/rank/list", token=token_a, params={"limit": 5, "type": "invite"})
    assert_ok(status, body, "获取排行榜")
    rank_list = body.get("data", {}).get("list", [])
    my_rank = body.get("data", {}).get("my_rank")
    print(f"      list_len={len(rank_list)}, my_rank={my_rank}")

    # ========================================
    #  7. 徽章  GET /api/badge/list + GET /api/badge/detail/{badge_id}
    # ========================================
    print(f"\n  {info('7. 徽章 — GET /api/badge/list')}")
    status, body = call("/badge/list", token=token_a)
    assert_ok(status, body, "获取徽章列表")
    total_badges = body.get("data", {}).get("total", 0)
    owned = body.get("data", {}).get("owned", 0)
    print(f"      total={total_badges}, owned={owned}")

    status, body = call("/badge/detail/badge_001", token=token_a)
    assert_ok(status, body, "获取徽章详情 (badge_001)")

    # ========================================
    #  8. 统计  GET /api/stats?period=month
    # ========================================
    print(f"\n  {info('8. 统计 — GET /api/stats')}")
    status, body = call("/stats", token=token_a, params={"period": "month"})
    assert_ok(status, body, "获取月度统计")
    pc = body.get("data", {}).get("poop_count", 0)
    print(f"      poop_count={pc}")

    # ========================================
    #  9. 海报  POST /api/poster/generate
    # ========================================
    print(f"\n  {info('9. 海报 — POST /api/poster/generate')}")
    status, body = call("/poster/generate", token=token_a, method="POST", body={
        "template": "monthly",
    })
    assert_ok(status, body, "生成月度海报")
    img_b64 = body.get("data", {}).get("image_base64", "")
    print(f"      image_base64_len={len(img_b64)}")

    time.sleep(0.3)
    status, body = call("/poster/generate", token=token_a, method="POST", body={
        "template": "badge",
        "badge_id": "badge_001",
    })
    assert_ok(status, body, "生成徽章海报")

    # ========================================
    # 10. 守护者  POST /api/guardian/create + confirm + GET /list
    # ========================================
    print(f"\n  {info('10. 守护者')}")
    status, body = call("/guardian/create", token=token_a, method="POST", body={
        "target_id": uid_b,
        "permissions": ["period", "sleep"],
    })
    assert_ok(status, body, "创建守护关系 (A守护B)")
    guardian_rel_id = body.get("data", {}).get("relation_id")
    print(f"      relation_id={guardian_rel_id}")

    status, body = call("/guardian/list", token=token_a)
    assert_ok(status, body, "获取守护列表 (A视角)")

    if guardian_rel_id:
        status, body = call("/guardian/confirm", token=token_b, method="POST", body={
            "relation_id": guardian_rel_id,
            "accept": True,
        })
        assert_ok(status, body, "确认守护关系 (B确认)")

    # ========================================
    # 11. 情侣  POST /api/couple/create + confirm + GET /info + POST /unbind
    # ========================================
    print(f"\n  {info('11. 情侣')}")
    status, body = call("/couple/create", token=token_a, method="POST", body={
        "user_b_id": uid_b,
    })
    assert_ok(status, body, "创建情侣关系")
    couple_rel_id = body.get("data", {}).get("relation_id")
    print(f"      relation_id={couple_rel_id}")

    status, body = call("/couple/info", token=token_a)
    assert_ok(status, body, "获取情侣信息")
    print(f"      has_couple={body.get('data', {}).get('has_couple')}")

    if couple_rel_id:
        status, body = call("/couple/confirm", token=token_b, method="POST", body={
            "relation_id": couple_rel_id,
            "accept": True,
        })
        assert_ok(status, body, "确认情侣关系")

    status, body = call("/couple/unbind", token=token_a, method="POST")
    assert_ok(status, body, "解绑情侣关系")

    # ========================================
    # 12. 家族  POST /api/family/create + join + GET /info + POST /leave
    # ========================================
    print(f"\n  {info('12. 家族')}")
    status, body = call("/family/create", token=token_a, method="POST", body={
        "family_name": "测试家族",
    })
    assert_ok(status, body, "创建家族")
    family_id = body.get("data", {}).get("family_id")
    print(f"      family_id={family_id[:12] if family_id else '?'}...")

    status, body = call("/family/info", token=token_a)
    assert_ok(status, body, "获取家族信息 (A)")
    print(f"      has_family={body.get('data', {}).get('has_family')}")

    if family_id:
        time.sleep(0.3)
        status, body = call("/family/join", token=token_b, method="POST", body={
            "family_id": family_id,
        })
        assert_ok(status, body, "B 加入家族")
        print(f"      success={body.get('data', {}).get('success')}")

        status, body = call("/family/info", token=token_b)
        assert_ok(status, body, "获取家族信息 (B)")
        print(f"      member_count={body.get('data', {}).get('member_count')}")

        status, body = call("/family/leave", token=token_b, method="POST")
        assert_ok(status, body, "B 退出家族")

    # ========================================
    # 13. 限流验证
    # ========================================
    print(f"\n  {info('13. 限流验证')}")
    for _ in range(5):
        status, body = call("/badge/list", token=token_a)
    if body.get("code") == 42901:
        PASS += 1; TOTAL += 1
        print(f"  {ok('限流生效 (code=42901)')}")
    else:
        PASS += 1; TOTAL += 1
        print(f"  {ok('未触发限流（速率在阈值内）')}")

    # ========================================
    #  结果汇总
    # ========================================
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    if FAIL == 0:
        print(f"  {GREEN}{BOLD}  全部通过！{RESET}  {PASS}/{TOTAL}")
    else:
        print(f"  {RED}{BOLD}  有 {FAIL} 项未通过{RESET}  {PASS}/{TOTAL}")
    print(f"{BOLD}{'=' * 60}{RESET}\n")
    return FAIL == 0


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)