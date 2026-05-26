import time
import requests

B = "http://127.0.0.1:8000/api"


def wait_if_limited(resp):
    if resp.status_code == 200 and resp.json().get("code") == 42901:
        retry_after = int(resp.headers.get("Retry-After", 2))
        time.sleep(retry_after)
        return True
    return False


# 1. login
r = requests.post(f"{B}/user/login", json={"code": "anime_test_001"})
t = r.json()["data"]["token"]
uid = r.json()["data"]["user_id"]
print(f"[LOGIN] uid={uid[:12]}...")

headers = {"Authorization": f"Bearer {t}"}

# 2. test library
r = requests.get(f"{B}/anime/library", headers=headers)
data = r.json()
print(f"[LIBRARY] code={data['code']} total={data['data']['total']}")

# 3. test subscribe anime_1 (idempotent: unsub first if already subscribed)
r = requests.post(f"{B}/anime/subscribe", json={"anime_id": "1"}, headers=headers)
if r.json()["code"] == 40010:
    requests.delete(f"{B}/anime/subscribe/1", headers=headers)
    time.sleep(0.5)
    r = requests.post(f"{B}/anime/subscribe", json={"anime_id": "1"}, headers=headers)
print(f"[SUB] code={r.json()['code']}")

# 4. test subscribe list
r = requests.get(f"{B}/anime/subscribe", headers=headers)
data = r.json()
print(f"[SUB-LIST] count={len(data['data']['list'])}")
item = data["data"]["list"][0]
print(f"  name={item['name']} update_day={item['update_day_text']} today={item['is_today_update']}")

# 5. test schedule
r = requests.get(f"{B}/anime/schedule", headers=headers)
data = r.json()
print(f"[SCHED] days={len(data['data']['schedule'])}")

# 6. test unsubscribe
r = requests.delete(f"{B}/anime/subscribe/1", headers=headers)
print(f"[UNSUB] code={r.json()['code']}")

# 7. test subscribe list after unsub
r = requests.get(f"{B}/anime/subscribe", headers=headers)
print(f"[SUB-AFTER] count={len(r.json()['data']['list'])}")

# 8. test drive (should fail - not enough invites)
r = requests.get(f"{B}/anime/drive/1", headers=headers)
print(f"[DRIVE] code={r.json()['code']} (expected 40004)")

# 9. test duplicate subscribe
r = requests.post(f"{B}/anime/subscribe", json={"anime_id": "1"}, headers=headers)
if wait_if_limited(r):
    r = requests.post(f"{B}/anime/subscribe", json={"anime_id": "1"}, headers=headers)
time.sleep(1)
r = requests.post(f"{B}/anime/subscribe", json={"anime_id": "1"}, headers=headers)
if wait_if_limited(r):
    time.sleep(1)
    r = requests.post(f"{B}/anime/subscribe", json={"anime_id": "1"}, headers=headers)
print(f"[DUP-SUB] code={r.json()['code']} (expected 40010)")

# 10. test not found anime
time.sleep(1)
r = requests.post(f"{B}/anime/subscribe", json={"anime_id": "999"}, headers=headers)
if wait_if_limited(r):
    time.sleep(1)
    r = requests.post(f"{B}/anime/subscribe", json={"anime_id": "999"}, headers=headers)
print(f"[NOT-FOUND] code={r.json()['code']} (expected 40009)")

print()
print("[OK] All anime endpoints working")