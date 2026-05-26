import time
import requests

BASE_URL = "http://127.0.0.1:8000"
API = f"{BASE_URL}/api"


class FlowTest:
    def __init__(self):
        self.base_url = BASE_URL
        self.data: dict = {}
        self.steps: list[tuple[str, bool]] = []

    def log(self, name: str, success: bool, msg: str = ""):
        status = "[PASS]" if success else "[FAIL]"
        print(f"  {status} {name}: {msg}")
        self.steps.append((name, success))

    def _call(self, method: str, path: str, body: dict | None = None,
              params: dict | None = None, expect_code: int = 0,
              step_name: str = ""):
        token = self.data.get("token_a", "")
        url = f"{self.base_url}{path}"
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        body_str = f" body={body}" if body else ""
        params_str = f" params={params}" if params else ""
        print(f"  > {method} {path}{params_str}{body_str}")

        if method == "GET":
            resp = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == "POST":
            resp = requests.post(url, headers=headers, json=body, timeout=10)
        else:
            resp = requests.request(method, url, headers=headers,
                                    json=body, params=params, timeout=10)

        rj = resp.json()
        code = rj.get("code", -1)
        msg = rj.get("message", "")

        if expect_code != 0:
            ok_flag = code == expect_code
            self.log(step_name, ok_flag,
                     f"code={code} (expected {expect_code}) {msg}")
            return code, rj.get("data"), ok_flag

        ok_flag = resp.status_code == 200 and code == 0
        self.log(step_name, ok_flag, f"code={code} {msg}")
        return code, rj.get("data"), ok_flag

    def test(self):
        start = time.time()

        try:
            requests.get(f"{self.base_url}/health", timeout=3)
            print("[OK] 服务可用\n")
        except Exception:
            print("[ERR] 服务不可用，请先启动后端")
            return False

        # ========================================================
        #  Flow 1: 新用户注册 -> 记录 -> 日历 -> 统计 -> 海报
        # ========================================================
        print("-" * 56)
        print("  Flow 1: 新用户注册 -> 记录 -> 验证完整链路")
        print("-" * 56)

        ts = str(int(time.time() * 1000))

        # 1.1 login user A
        code, data, ok = self._call("POST", "/api/user/login",
            body={"code": f"flow_a_{ts}"}, step_name="1.1 用户A登录")
        if not ok: return False
        self.data["token_a"] = data["token"]
        self.data["user_a"] = data["user_id"]
        self.data["is_new"] = data["is_new"]
        assert data["is_new"], "新用户应该 is_new=True"

        # 1.2 get user info
        code, data, ok = self._call("GET", "/api/user/info",
            step_name="1.2 获取用户信息")
        if not ok: return False
        assert data["invite_count"] == 0, "invite_count 应为0"
        assert data["continuous_days"] == 0, "continuous_days 应为0"

        # 1.3 create record
        today = time.strftime("%Y-%m-%d")
        code, data, ok = self._call("POST", "/api/record/create", body={
            "record_type": "poop",
            "record_date": today,
            "record_value": {"count": 1},
        }, step_name="1.3 创建拉屎记录")
        if not ok: return False
        assert data["continuous_days"] == 1, "连续天数应为1"
        self.data["record_id"] = data["record_id"]

        # 1.4 duplicate -> 40003
        code, data, ok = self._call("POST", "/api/record/create", body={
            "record_type": "poop",
            "record_date": today,
            "record_value": {"count": 1},
        }, expect_code=40003, step_name="1.4 重复记录拦截 (40003)")

        # 1.5 calendar
        now = time.localtime()
        code, data, ok = self._call("GET", "/api/calendar",
            params={"year": now.tm_year, "month": now.tm_mon},
            step_name="1.5 获取日历数据")
        if not ok: return False
        records_map = data.get("records_map", {})
        assert today in records_map, f"日历应包含今天 {today}"

        # 1.6 today status
        code, data, ok = self._call("GET", "/api/today/status",
            step_name="1.6 获取今日状态")
        if not ok: return False
        features = data.get("features", {})
        assert features.get("poop", {}).get("recorded"), "poop 应为已记录"

        # 1.7 stats
        code, data, ok = self._call("GET", "/api/stats",
            params={"period": "month"}, step_name="1.7 获取月度统计")
        if not ok: return False
        assert data["poop_count"] >= 1, "poop 次数应 >= 1"

        # 1.8 poster
        code, data, ok = self._call("POST", "/api/poster/generate",
            body={"template": "monthly"}, step_name="1.8 生成月度海报")
        if not ok: return False
        assert len(data.get("image_base64", "")) > 0, "海报应返回 base64"

        print("  Flow 1 完成 OK\n")

        # ========================================================
        #  Flow 2: 邀请裂变 -> 进度 -> 排行榜 -> 徽章
        # ========================================================
        print("-" * 56)
        print("  Flow 2: 邀请裂变 -> 进度 -> 排行榜 -> 徽章")
        print("-" * 56)

        # 2.1 login user B
        code, data, ok = self._call("POST", "/api/user/login",
            body={"code": f"flow_b_{ts}"}, step_name="2.1 用户B登录")
        if not ok: return False
        self.data["token_b"] = data["token"]
        self.data["user_b"] = data["user_id"]

        # 2.2 A invite B (B's openid = code = flow_b_{ts})
        code, data, ok = self._call("POST", "/api/invite/create", body={
            "invitee_openid": f"flow_b_{ts}",
            "invitee_device": "flow_test_device",
        }, step_name="2.2 A 邀请 B")
        if not ok: return False
        assert data["invite_count"] >= 1, "邀请人数应 >= 1"

        # 2.3 invite progress
        code, data, ok = self._call("GET", "/api/invite/progress",
            step_name="2.3 获取邀请进度")
        if not ok: return False
        assert data["current"] >= 1, "进度应 >= 1"

        # 2.4 rank list
        code, data, ok = self._call("GET", "/api/rank/list",
            params={"limit": 5, "type": "invite"},
            step_name="2.4 获取排行榜")
        if not ok: return False
        assert len(data.get("list", [])) > 0, "排行榜应有数据"

        # 2.5 badges
        code, data, ok = self._call("GET", "/api/badge/list",
            step_name="2.5 获取徽章列表")
        if not ok: return False
        assert data["total"] > 0, "应有徽章定义"

        # 2.6 badge detail
        code, data, ok = self._call("GET", "/api/badge/detail/badge_001",
            step_name="2.6 获取徽章详情")
        if not ok: return False
        assert data.get("name"), "徽章应有名称"

        # 2.7 badge poster
        code, data, ok = self._call("POST", "/api/poster/generate", body={
            "template": "badge", "badge_id": "badge_001",
        }, step_name="2.7 生成徽章海报")
        if not ok: return False

        print("  Flow 2 完成 OK\n")

        # ========================================================
        #  Flow 3: 社交关系 -> 守护 -> 情侣 -> 家族
        # ========================================================
        print("-" * 56)
        print("  Flow 3: 社交关系 -> 守护 -> 情侣 -> 家族")
        print("-" * 56)

        # 3.1 guardian create (A -> B)
        code, data, ok = self._call("POST", "/api/guardian/create", body={
            "target_id": self.data["user_b"],
            "permissions": ["period", "sleep"],
        }, step_name="3.1 A 创建守护关系")
        if not ok: return False
        guardian_rel_id = data.get("relation_id")
        assert data["status"] == "pending", "状态应为 pending"

        # 3.2 guardian list (A) — pending relation may not show yet
        code, data, ok = self._call("GET", "/api/guardian/list",
            step_name="3.2 查看守护列表")
        if not ok: return False
        print(f"      my_guardians={len(data.get('my_guardians', []))} "
              f"guardians_of_me={len(data.get('guardians_of_me', []))}")

        # 3.3 guardian confirm (B)
        self.data["token_a"], self.data["token_b"] = \
            self.data["token_b"], self.data["token_a"]
        code, data, ok = self._call("POST", "/api/guardian/confirm", body={
            "relation_id": guardian_rel_id, "accept": True,
        }, step_name="3.3 B 确认守护")
        self.data["token_a"], self.data["token_b"] = \
            self.data["token_b"], self.data["token_a"]
        if not ok: return False

        # 3.3b guardian list (confirmed)
        code, data2, ok2 = self._call("GET", "/api/guardian/list",
            step_name="3.3b 确认后查看守护列表")
        if not ok2: return False
        assert len(data2.get("my_guardians", [])) > 0, "确认后 my_guardians 应包含 B"

        # 3.4 couple create (A -> B)
        code, data, ok = self._call("POST", "/api/couple/create", body={
            "user_b_id": self.data["user_b"],
        }, step_name="3.4 A 创建情侣关系")
        if not ok: return False
        couple_rel_id = data.get("relation_id")
        assert data["status"] == "pending", "状态应为 pending"

        # 3.5 couple info (pending state)
        code, data, ok = self._call("GET", "/api/couple/info",
            step_name="3.5 查看情侣信息 (pending)")
        if not ok: return False
        print(f"      has_couple={data.get('has_couple')} (pending)")

        # 3.6 couple confirm (B)
        self.data["token_a"], self.data["token_b"] = \
            self.data["token_b"], self.data["token_a"]
        code, data, ok = self._call("POST", "/api/couple/confirm", body={
            "relation_id": couple_rel_id, "accept": True,
        }, step_name="3.6 B 确认情侣")
        self.data["token_a"], self.data["token_b"] = \
            self.data["token_b"], self.data["token_a"]
        if not ok: return False

        # 3.6b couple info (confirmed)
        code, data3, ok3 = self._call("GET", "/api/couple/info",
            step_name="3.6b 查看情侣信息 (confirmed)")
        if not ok3: return False
        assert data3.get("has_couple"), "确认后 has_couple 应为 True"

        # 3.7 couple unbind
        code, data, ok = self._call("POST", "/api/couple/unbind",
            step_name="3.7 A 解绑情侣")
        if not ok: return False

        # 3.8 family create
        family_ts = str(int(time.time() * 1000))
        code, data, ok = self._call("POST", "/api/family/create", body={
            "family_name": f"flow_test_family_{family_ts}",
        }, step_name="3.8 A 创建家族")
        if not ok: return False
        family_id = data.get("family_id")

        # 3.9 family info (A)
        code, data, ok = self._call("GET", "/api/family/info",
            step_name="3.9 查看家族信息")
        if not ok: return False
        assert data.get("has_family"), "A 应在家族中"

        # 3.10 family join (B)
        self.data["token_a"], self.data["token_b"] = \
            self.data["token_b"], self.data["token_a"]
        code, data, ok = self._call("POST", "/api/family/join", body={
            "family_id": family_id,
        }, step_name="3.10 B 加入家族")
        if not ok: return False

        # 3.11 family info (B)
        code, data, ok = self._call("GET", "/api/family/info",
            step_name="3.11 B 查看家族信息")
        if not ok: return False
        assert data["member_count"] >= 2, "家族成员应 >= 2"

        # 3.12 family leave (B)
        code, data, ok = self._call("POST", "/api/family/leave",
            step_name="3.12 B 退出家族")
        self.data["token_a"], self.data["token_b"] = \
            self.data["token_b"], self.data["token_a"]
        if not ok: return False

        # 3.13 no-auth intercept
        self.data["token_a"] = ""
        code, data, ok = self._call("GET", "/api/user/info",
            expect_code=40101, step_name="3.13 无Token拦截 (40101)")

        print("  Flow 3 完成 OK\n")

        # ========================================================
        #  Report
        # ========================================================
        total = len(self.steps)
        passed = sum(1 for _, s in self.steps if s)
        elapsed = time.time() - start
        print("=" * 56)
        if passed == total:
            print(f"  [REPORT] ALL PASS  {passed}/{total}  {elapsed:.1f}s")
        else:
            print(f"  [REPORT] {passed}/{total}  {elapsed:.1f}s")
            for fs in [n for n, s in self.steps if not s]:
                print(f"     - {fs}")
        print("=" * 56 + "\n")
        return passed == total


if __name__ == "__main__":
    test = FlowTest()
    success = test.test()
    exit(0 if success else 1)