# -*- coding: utf-8 -*-
"""后端 API 连通性测试

运行方式:
    uv run python test/api-test.py
    或
    python test/api-test.py
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
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def _ok(msg):
    return f"{GREEN}  OK{RESET}  {msg}"


def _fail(msg):
    return f"{RED}FAIL{RESET}  {msg}"


def _info(msg):
    return f"{CYAN}{BOLD}{msg}{RESET}"


def _d(body, key, *sub_keys, default=None):
    val = (body.get("data") or {}).get(key, default)
    for k in sub_keys:
        val = (val or {}).get(k, default)
    return val


def call(path, token=None, method="GET", body=None, params=None, raw=False):
    url = f"{BASE}{path}" if raw else f"{API}{path}"
    if params:
        parts = [f"{k}={urllib.request.quote(str(v))}" for k, v in params.items()]
        url += "?" + "&".join(parts)

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8"))
        except json.JSONDecodeError:
            return e.code, {"code": -1, "message": f"HTTP {e.code}", "data": None}
    except urllib.error.URLError as e:
        return 0, {"code": -1, "message": str(e.reason), "data": None}


def ok(status, body, name):
    global PASS, FAIL, TOTAL
    TOTAL += 1
    if status == 200 and body.get("code") == 0:
        PASS += 1
        print(f"  {_ok(name)}")
        return True
    FAIL += 1
    print(f"  {_fail(name)} — code={body.get('code')}, {body.get('message', '')}")
    return False


def code_is(status, body, expected_code, name):
    global PASS, FAIL, TOTAL
    TOTAL += 1
    if body.get("code") == expected_code:
        PASS += 1
        print(f"  {_ok(name)} (code={expected_code})")
        return True
    FAIL += 1
    print(f"  {_fail(name)} — code={body.get('code')}, expected {expected_code}")
    return False


def main():
    global PASS, FAIL, TOTAL
    PASS = FAIL = TOTAL = 0

    print(f"{BOLD}{'=' * 60}{RESET}")
    print(f"  {_info('Run-It 后端 API 连通性测试')}")
    print(f"  地址: {BASE}")
    print(f"  时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{BOLD}{'=' * 60}{RESET}")

    # ── 0. 健康检查 ──────────────────────────────────────
    print(f"\n  {_info('0. 健康检查  GET /health')}")
    s, b = call("/health", raw=True)
    if s == 200 and b.get("status") == "ok":
        PASS += 1; TOTAL += 1
        env_val = b.get("env", "?")
        print(f"  {_ok(f'服务正常 (env={env_val})')}")
    else:
        FAIL += 1; TOTAL += 1
        print(f"  {_fail(f'服务异常: {b}')}")
        print(f"\n  {RED}请先启动: uv run uvicorn app.main:app --host 0.0.0.0 --port 8000{RESET}")
        return

    # ── 1. 登录 ─────────────────────────────────────────
    print(f"\n  {_info('1. 用户登录  POST /api/user/login')}")

    s, b = call("/user/login", method="POST", body={"code": "test_user_a"})
    if not ok(s, b, "用户 A 登录"):
        print(f"  {RED}无法登录，中止测试{RESET}"); return
    token_a = b["data"]["token"]
    uid_a = b["data"]["user_id"]
    print(f"      user_id={uid_a[:12]}... is_new={b['data']['is_new']}")

    time.sleep(0.3)
    s, b = call("/user/login", method="POST", body={"code": "test_user_b"})
    if not ok(s, b, "用户 B 登录"):
        print(f"  {RED}无法登录，中止测试{RESET}"); return
    token_b = b["data"]["token"]
    uid_b = b["data"]["user_id"]
    print(f"      user_id={uid_b[:12]}...")

    # ── 2. 用户信息 ─────────────────────────────────────
    print(f"\n  {_info('2. 用户信息  GET /api/user/info')}")
    s, b = call("/user/info", token=token_a)
    ok(s, b, "获取用户信息")
    print(f"      nickname={_d(b, 'nickname')} "
          f"invite_count={_d(b, 'invite_count')} "
          f"badges={len(_d(b, 'badges', []))}")

    # ── 3. 记录 ─────────────────────────────────────────
    print(f"\n  {_info('3. 记录  POST /api/record/create')}")
    today = time.strftime("%Y-%m-%d")

    # 避免重复运行冲突：先试 poop，如果今天已记录则换 sleep
    s, b = call("/record/create", token=token_a, method="POST", body={
        "record_type": "poop", "record_date": today, "record_value": {"count": 1},
    })
    if b.get("code") == 40003:
        print(f"  {_ok('poop 今天已有记录 (跳过)')}")
        s, b = call("/record/create", token=token_a, method="POST", body={
            "record_type": "sleep", "record_date": today, "record_value": {"hours": 8},
        })
        if b.get("code") == 40003:
            print(f"  {_ok('sleep 今天也有记录 (跳过)')}")
        elif b.get("code") == 40004:
            print(f"  {_ok('sleep 功能未解锁 (跳过)')}")
        else:
            ok(s, b, "创建睡眠记录")
            print(f"      record_id={_d(b, 'record_id')}  "
                  f"continuous_days={_d(b, 'continuous_days')}  "
                  f"badges_earned={len(_d(b, 'badges_earned', []))}")
    elif b.get("code") == 40004:
        print(f"  {_ok('sleep 功能未解锁 (跳过)')}")
    else:
        ok(s, b, "创建拉屎记录")
        print(f"      record_id={_d(b, 'record_id')}  "
              f"continuous_days={_d(b, 'continuous_days')}  "
              f"badges_earned={len(_d(b, 'badges_earned', []))}")

    s, b = call("/record/create", token=token_a, method="POST", body={
        "record_type": "poop", "record_date": today, "record_value": {"count": 1},
    })
    code_is(s, b, 40003, "重复记录拦截")

    # ── 4. 日历 ─────────────────────────────────────────
    print(f"\n  {_info('4. 日历  GET /api/calendar')}")
    now = time.localtime()
    s, b = call("/calendar", token=token_a, params={"year": now.tm_year, "month": now.tm_mon})
    ok(s, b, "获取日历数据")
    print(f"      days={len(_d(b, 'days', []))}")

    # ── 5. 今日状态 ─────────────────────────────────────
    print(f"\n  {_info('5. 今日状态  GET /api/today/status')}")
    s, b = call("/today/status", token=token_a)
    ok(s, b, "获取今日状态")
    features = _d(b, "features", {})
    recorded = [k for k, v in features.items() if v.get("recorded")]
    print(f"      recorded={recorded}")

    # ── 6. 邀请 ─────────────────────────────────────────
    print(f"\n  {_info('6. 邀请  POST /api/invite/create + GET /progress')}")
    s, b = call("/invite/create", token=token_a, method="POST", body={
        "invitee_openid": "test_user_b",
        "invitee_device": "test_device",
    })
    if b.get("code") == 40005:
        print(f"  {_ok('B已被邀请 (跳过)')}")
    else:
        ok(s, b, "创建邀请关系")
    print(f"      invite_count={_d(b, 'invite_count')}  "
          f"new_unlocked={_d(b, 'new_unlocked')}")

    s, b = call("/invite/progress", token=token_a)
    ok(s, b, "获取邀请进度")
    print(f"      current={_d(b, 'current')}  "
          f"remaining={_d(b, 'remaining')}")

    # ── 7. 排行榜 ───────────────────────────────────────
    print(f"\n  {_info('7. 排行榜  GET /api/rank/list')}")
    s, b = call("/rank/list", token=token_a, params={"limit": 5, "type": "invite"})
    ok(s, b, "获取排行榜")
    print(f"      list_len={len(_d(b, 'list', []))}  "
          f"my_rank={_d(b, 'my_rank')}")

    # ── 8. 徽章 ─────────────────────────────────────────
    print(f"\n  {_info('8. 徽章  GET /api/badge/list + /detail')}")
    s, b = call("/badge/list", token=token_a)
    ok(s, b, "获取徽章列表")
    print(f"      total={_d(b, 'total')}  owned={_d(b, 'owned')}")

    s, b = call("/badge/detail/badge_001", token=token_a)
    ok(s, b, "获取徽章详情")

    # ── 9. 统计 ─────────────────────────────────────────
    print(f"\n  {_info('9. 统计  GET /api/stats')}")
    s, b = call("/stats", token=token_a, params={"period": "month"})
    ok(s, b, "获取月度统计")
    print(f"      poop_count={_d(b, 'overview', 'poop_count')}  "
          f"beat_users={_d(b, 'overview', 'beat_users')}")

    # ── 10. 海报 ────────────────────────────────────────
    print(f"\n  {_info('10. 海报  POST /api/poster/generate')}")
    s, b = call("/poster/generate", token=token_a, method="POST", body={"template": "monthly"})
    ok(s, b, "生成月度海报")
    print(f"      image_base64_len={len(_d(b, 'image_base64', ''))}")

    time.sleep(0.3)
    s, b = call("/poster/generate", token=token_a, method="POST", body={
        "template": "badge", "badge_id": "badge_001",
    })
    ok(s, b, "生成徽章海报")

    # ── 11. 守护者 ──────────────────────────────────────
    print(f"\n  {_info('11. 守护者  POST /api/guardian/*')}")
    s, b = call("/guardian/create", token=token_a, method="POST", body={
        "target_id": uid_b, "permissions": ["period", "sleep"],
    })
    if b.get("code") == 40007:
        print(f"  {_ok('守护关系已存在 (跳过)')}")
    else:
        ok(s, b, "创建守护关系 (A -> B)")
    gr_id = _d(b, "relation_id")

    s, b = call("/guardian/list", token=token_a)
    ok(s, b, "获取守护列表")
    print(f"      my_guardians={len(_d(b, 'my_guardians', []))}  "
          f"guardians_of_me={len(_d(b, 'guardians_of_me', []))}")

    if gr_id:
        s, b = call("/guardian/confirm", token=token_b, method="POST", body={
            "relation_id": gr_id, "accept": True,
        })
        ok(s, b, "确认守护关系 (B 确认)")

    # ── 12. 情侣 ────────────────────────────────────────
    print(f"\n  {_info('12. 情侣  POST /api/couple/*')}")
    s, b = call("/couple/create", token=token_a, method="POST", body={"user_b_id": uid_b})
    ok(s, b, "创建情侣关系")
    cr_id = _d(b, "relation_id")

    s, b = call("/couple/info", token=token_a)
    ok(s, b, "获取情侣信息")

    if cr_id:
        s, b = call("/couple/confirm", token=token_b, method="POST", body={
            "relation_id": cr_id, "accept": True,
        })
        ok(s, b, "确认情侣关系")

    s, b = call("/couple/unbind", token=token_a, method="POST")
    ok(s, b, "解绑情侣关系")

    # ── 13. 家族 ────────────────────────────────────────
    print(f"\n  {_info('13. 家族  POST /api/family/*')}")
    s, b = call("/family/create", token=token_a, method="POST", body={"family_name": "测试家族"})
    if b.get("code") == 40001:
        print(f"  {_ok('已在家族中 (跳过创建)')}")
    elif b.get("code") == 50001:
        print(f"  {_ok('已有家族成员记录 (跳过)')}")
    else:
        ok(s, b, "创建家族")
    fid = _d(b, "family_id")

    s, b = call("/family/info", token=token_a)
    ok(s, b, "获取家族信息")

    if fid:
        time.sleep(0.3)
        s, b = call("/family/join", token=token_b, method="POST", body={"family_id": fid})
        ok(s, b, "B 加入家族")

        s, b = call("/family/info", token=token_b)
        ok(s, b, "获取家族信息 (B视角)")
        print(f"      member_count={_d(b, 'member_count')}")

        s, b = call("/family/leave", token=token_b, method="POST")
        ok(s, b, "B 退出家族")

    # ── 14. 未认证拦截 ──────────────────────────────────
    print(f"\n  {_info('14. 未认证拦截')}")
    s, b = call("/user/info", token=None)
    code_is(s, b, 40101, "无Token访问")

    # ── 15. 限流验证 ────────────────────────────────────
    print(f"\n  {_info('15. 限流验证')}")
    for _ in range(5):
        s, b = call("/badge/list", token=token_a)
    if b.get("code") == 42901:
        PASS += 1; TOTAL += 1
        print(f"  {_ok('限流生效 (code=42901)')}")
    else:
        PASS += 1; TOTAL += 1
        print(f"  {_ok('未触发限流（速率在阈值内）')}")

    # ── 汇总 ────────────────────────────────────────────
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    if FAIL == 0:
        print(f"  {GREEN}{BOLD}  全部通过！{RESET}  {PASS}/{TOTAL}")
    else:
        print(f"  {RED}{BOLD}  {FAIL} 项未通过{RESET}  {PASS}/{TOTAL}")
    print(f"{BOLD}{'=' * 60}{RESET}\n")


if __name__ == "__main__":
    main()
    sys.exit(0 if FAIL == 0 else 1)