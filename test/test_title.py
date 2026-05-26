import json, re

for fname in ["影视剧.json", "电影.json", "4K.json"]:
    with open(f"date/{fname}", encoding="utf-8") as f:
        data = json.load(f)
    entries = data.get("entries", [])
    print(f"=== {fname}: {len(entries)} 条 ===")
    for e in entries[:3]:
        t = e.get("title", "")
        print(f"  title={t!r}")
    print()