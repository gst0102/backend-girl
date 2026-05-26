# 金山文档抓取工具 — 接口文档

## 项目概述

自动抓取 [kdocs.cn](https://www.kdocs.cn) 金山智能文档内容，提取剧集条目及网盘链接，支持增量更新和持续监听。

- **数据源**：金山智能文档（ProseMirror JSON 结构）
- **提取引擎**：Playwright 无头 Chromium → `COLLABX.editor.getJSON()`
- **核心特色**：以 `title` 为主键增量合并，只更新动态变化的字段

---

## 文件结构

```
girl-client/
├── fetch_kdocs.py          # Python 主脚本（推荐）— Playwright 无头 + 增量监听
├── fetch_kdocs.ps1         # PowerShell 脚本 — 基于 OpenCLI 浏览器驱动
├── kdocs_extract.js        # JS 提取脚本（OpenCLI 用）
├── kdocs_dismiss_login.js  # JS 登录弹窗关闭脚本（OpenCLI 用）
├── kdocs_热门剧.json        # 参考输出样例
└── README.md               # 本文档
```

---

## 安装

### Python 版本（推荐）

```bash
pip install playwright
playwright install chromium
```

### PowerShell 版本

```bash
npm install -g @jackwener/opencli
# 需先安装 Chrome + OpenCLI Chrome 扩展
```

---

## 使用方式

### Python 单次抓取

```bash
python fetch_kdocs.py
python fetch_kdocs.py --url "https://www.kdocs.cn/l/xxxxx" --output result.json
```

### Python 持续监听

```bash
# 默认每 5 分钟检查一次
python fetch_kdocs.py --watch

# 自定义间隔（秒）
python fetch_kdocs.py --watch --interval 600

# 首次全量覆盖已有的 JSON
python fetch_kdocs.py --watch --reset
```

监听模式运行后会持续轮询，输出变化统计：

```
[WATCH] Cycle #1  2026-05-23 10:00:00
  Entries: 3  |  +3 new  ~0 updated  =0 unchanged

[WATCH] Cycle #2  2026-05-23 10:05:00
  Entries: 4  |  +1 new  ~2 updated  =1 unchanged
    [2] 主角 → 更 28
    [3] 家业 → 更 15
    [4] 新剧 → 新增
```

`Ctrl+C` 优雅退出，自动保存最后一次结果。

---

## CLI 输入参数

| 参数 | 简写 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--url` | `-u` | string | `https://www.kdocs.cn/l/co72a28MWkmI` | 金山文档链接 |
| `--output` | `-o` | string | `kdocs_output.json` | 输出 JSON 路径 |
| `--watch` | `-w` | flag | — | 启用持续监听模式 |
| `--interval` | `-i` | int | `300` | 监听间隔（秒），最小建议 60 |
| `--reset` | — | flag | — | 监听模式下首次清空已有数据 |

---

## JSON 输出 Schema

### 顶层结构

```json
{
  "meta":           { ... },   // 文档元信息
  "instructions":   { ... },   // 使用说明
  "entries":        [ ... ],   // 剧集条目列表（增量累积）
  "total_entries":  3,         // 当前条目总数
  "total_text_items": 27       // 文档段落总数
}
```

### `meta` — 元信息

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `source` | string | 数据来源 | `"金山文档 (kdocs.cn)"` |
| `url` | string | 文档链接 | `"https://www.kdocs.cn/l/co72a28MWkmI"` |
| `title` | string | 文档标题 | `"热门剧"` |
| `fetch_time` | string | 首次抓取日期 | `"2026-05-23"` |
| `last_fetch_full` | string | 最近一次完整抓取时间（监听模式追加） | `"2026-05-23 10:05:00"` |
| `update_date` | string | 文档更新日期（从章节标题正则提取） | `"2026-05-22"` |
| `update_time` | string | 文档更新时间（从 "HH:MM更新" 提取） | `"00:05"` |
| `update_note` | string | 更新时间说明 | `"文档章节标题为 2026.5.22（热门更新）..."` |
| `editor` | string | 编辑者昵称（从 "xxx 今天 HH:MM更新" 提取） | `"小丸子4K"` |

### `instructions` — 使用说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `search_method` | string | 搜索方法描述 |
| `notice` | string[] | 注意事项列表 |
| `solution_steps` | string[] | 操作步骤（①②③④⑤） |

### `entries[]` — 条目

| 字段 | 类型 | 可能为 null | 说明 | 示例 |
|------|------|-------------|------|------|
| `index` | int | — | 序号（增量模式下保持不变） | `1` |
| `title` | string | — | 剧名（主键，用于增量匹配） | `"良陈美锦"` |
| `quality` | string | ✅ | 清晰度 | `"1080P"` |
| `episode` | string | ✅ | 集数 | `"更 40"` |
| `status` | string | ✅ | 状态 | `"超前完结"` |
| `fetch_time` | string | — | 该条目最近一次抓取日期 | `"2026-05-23"` |
| `update_date` | string | ✅ | 文档更新日期 | `"2026-05-22"` |
| `update_time` | string | ✅ | 文档更新时间 | `"00:05"` |
| `links` | object | — | 网盘链接组 | 见下方 |

### `entries[].links` — 链接组

| 字段 | 类型 | 说明 |
|------|------|------|
| `links.baidu` | object | 百度网盘 |
| `links.baidu.url` | string | 百度链接，无则为 `""` |
| `links.baidu.password` | string | 提取码，无则为 `""` |
| `links.quark` | string | 夸克链接，无则为 `""` |
| `links.4k` | string | 4K 清晰度备注或文档链接 |

---

## 增量更新机制

每次抓取后，以 `title` 为主键对比已有条目：

```
当前文档的条目
    │
    ├─ 新条目 (title 未在 JSON 中出现过)
    │   └─ 追加到 entries 末尾，分配新 index
    │
    ├─ 已有条目 (title 已存在)
    │   ├─ 动态字段未变化 → 原样保留（不修改 fetch_time）
    │   └─ 动态字段有变化 → 只更新变化的字段
    │       变更字段：quality / episode / status / baidu_url / baidu_password / quark_url / k4_note
    │
    └─ JSON 中但当前文档中消失的条目 → 保留不删除（历史数据）
```

### 指纹比对

仅对以下 7 个动态字段做指纹对比：

```
quality | episode | status | baidu_url | baidu_password | quark_url | k4_note
```

`title` 和 `fetch_time` 不参与指纹比对（title 用于匹配，fetch_time 是元数据）。

---

## 错误处理

| 场景 | 行为 |
|------|------|
| Playwright 未安装 | 打印安装提示并退出 |
| 页面加载超时 (30s) | 抛出 RuntimeError |
| Canvas 未出现 (20s) | 继续等待 COLLABX |
| COLLABX 未就绪 (60s) | 抛出 RuntimeError（第 5 次重试时触发滚动激活懒加载） |
| JSON 解析失败 | 保留原文件不变，打印错误 |
| 监听模式下单次抓取失败 | 打印错误，继续下一轮 |
| 磁盘写入 | 先写 `.tmp` 文件再 rename（原子操作，不会出现半截文件） |

---

## 注意事项

1. **登录态**：需要在 Chrome 中登录 kdocs.cn，Playwright 使用系统默认用户数据目录
2. **监听间隔**：建议 ≥ 60 秒，过于频繁可能触发反爬
3. **告警**：如果 kdocs.cn 改版导致 `COLLABX.editor.getJSON()` 不可用，需适配新的数据获取方式
4. **编码**：输出 JSON 使用 UTF-8 编码，`ensure_ascii=False` 保留中文原文



`

```

输出格式模版：
{
  "meta": {
    "source": "金山文档 (kdocs.cn)",
    "url": "https://www.kdocs.cn/l/co72a28MWkmI",
    "title": "热门剧",
    "fetch_time": "2026-05-23",
    "update_date": "2026-05-22",
    "update_time": "00:05",
    "update_note": "文档章节标题为 2026.5.22（热门更新），编辑者显示 今天 00:05更新",
    "editor": "小丸子4K"
  },
  "instructions": {
    "search_method": "右上角登录 >> 右上角三个横线 >> 查找和替换 >> 输入关键字 >> 点击搜索（搜不到就是暂无资源）",
    "notice": [
      "先转存 ⇨ 再观看 ⇨ 避失效 ⇨ 耽误看 ⇨ 文件 ⇨ 补档慢",
      "夸克和谐严重，尽量使用百度",
      "夸克缺集数就是和谐了"
    ],
    "solution_steps": [
      "①复制网盘链接 ⇨",
      "②打开网盘APP ⇨",
      "③自动弹出文件夹 ⇨",
      "④点击转存 ⇨",
      "⑤回到自己网盘中播放"
    ]
  },
  "entries": [
    {
      "index": 1,
      "title": "良陈美锦",
      "quality": "1080P",
      "episode": "更 40",
      "status": "超前完结",
      "fetch_time": "2026-05-23",
      "update_date": "2026-05-22",
      "update_time": "00:05",
      "links": {
        "baidu": {
          "url": "https://pan.baidu.com/s/1ZxOTd0VtCpDIJwbHcBn_Sw",
          "password": "1120"
        },
        "quark": "https://pan.quark.cn/s/18ada21fca9e",
        "4k": "热剧【4K⁺】清晰度专用文档(NEW)"
      }
    },
    {
      "index": 2,
      "title": "主角",
      "quality": "1080P",
      "episode": "更 27",
      "status": null,
      "fetch_time": "2026-05-23",
      "update_date": "2026-05-22",
      "update_time": "00:05",
      "links": {
        "baidu": {
          "url": "https://pan.baidu.com/s/1u7xsrtn7EQGShKsIjkR6lg",
          "password": "1120"
        },
        "quark": "https://pan.quark.cn/s/10a6450bb381",
        "4k": "热剧【4K⁺】清晰度专用文档(NEW)"
      }
    },
    {
      "index": 3,
      "title": "家业",
      "quality": "1080P",
      "episode": "更 14",
      "status": null,
      "fetch_time": "2026-05-23",
      "update_date": "2026-05-22",
      "update_time": "00:05",
      "links": {
        "baidu": {
          "url": "https://pan.baidu.com/s/1b_FGdz6TJzfuRSX3EywqGQ",
          "password": "1120"
        },
        "quark": "https://pan.quark.cn/s/d97b498fa9c2",
        "4k": "热剧【4K⁺】清晰度专用文档(NEW)"
      }
    }
  ],
  "total_entries": 3,
  "total_text_items": 27
}
```

`