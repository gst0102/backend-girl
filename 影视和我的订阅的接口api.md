# 影视库 & 我的订阅 — 第三方接入接口文档

> 版本：1.0  
> 基础域名：`https://your-api-domain.com`  
> 认证方式：微信小程序登录 Token，放入请求头 `Authorization: Bearer <token>`

---

## 目录

1. [影视库列表](#1-影视库列表)
2. [我的订阅列表](#2-我的订阅列表)
3. [订阅番剧](#3-订阅番剧)
4. [取消订阅番剧](#4-取消订阅番剧)
5. [获取网盘链接 & 催更](#5-获取网盘链接--催更)
6. [附录：数据结构 & 错误码](#6-附录)

---

## 1. 影视库列表

获取影视资源列表，按类型筛选，支持关键词搜索和分页。

| 项目 | 内容 |
|------|------|
| 方法 | GET |
| 路径 | `/api/anime/library` |
| 认证 | 需要（Bearer Token） |

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 否 | 资源类型。`anime`=番剧(默认)、`movie`=电影、`4k`=4K资源 |
| keyword | string | 否 | 搜索关键词，模糊匹配标题 |
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页数量，默认 20，最大 100 |

**响应体：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 150,
    "list": [
      {
        "anime_id": "abc123",
        "title": "庆余年 第二季（1080P）超前点播",
        "quality": "1080P",
        "episode": "更至36集",
        "status": "更新中",
        "baidu_url": "https://pan.baidu.com/s/xxx",
        "baidu_password": "abcd",
        "quark_url": "https://pan.quark.cn/s/yyy",
        "update_time": "2026-05-26",
        "is_subscribed": true,
        "is_reminded": false
      }
    ]
  }
}
```

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| anime_id | string | 番剧ID，用于订阅/取链操作 |
| title | string | 完整标题（保留括号内画质等信息） |
| quality | string | 画质：`1080P` / `4K` / `720P` 等 |
| episode | string | 当前更新进度 |
| status | string | 状态：`更新中` / `完结` / `预告` |
| baidu_url | string | 百度网盘链接 |
| baidu_password | string | 百度网盘提取码 |
| quark_url | string | 夸克网盘链接 |
| update_time | string | 最近更新时间 |
| is_subscribed | boolean | 当前用户是否已订阅 |
| is_reminded | boolean | 当前用户是否已催更 |

---

## 2. 我的订阅列表

获取当前用户已订阅的番剧列表。

| 项目 | 内容 |
|------|------|
| 方法 | GET |
| 路径 | `/api/anime/subscribe` |
| 认证 | 需要（Bearer Token） |

**查询参数：** 无

**响应体：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "list": [
      {
        "anime_id": "abc123",
        "title": "庆余年 第二季（1080P）超前点播",
        "quality": "1080P",
        "episode": "更至36集",
        "status": "更新中",
        "baidu_url": "https://pan.baidu.com/s/xxx",
        "baidu_password": "abcd",
        "quark_url": "https://pan.quark.cn/s/yyy",
        "update_time": "2026-05-26",
        "is_subscribed": true
      }
    ]
  }
}
```

> 字段含义同 [影视库列表](#1-影视库列表)

---

## 3. 订阅番剧

用户订阅指定番剧，用于后续接收更新提醒和快速访问。

| 项目 | 内容 |
|------|------|
| 方法 | POST |
| 路径 | `/api/anime/subscribe` |
| 认证 | 需要（Bearer Token） |
| Content-Type | application/json |

**请求体：**

```json
{
  "anime_id": "abc123"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| anime_id | string | 是 | 番剧ID（来自影视库列表的 `anime_id`） |

**响应体（成功）：**

```json
{
  "code": 0,
  "message": "success",
  "data": { "success": true }
}
```

**响应体（番剧不存在）：**

```json
{
  "code": 40401,
  "message": "番剧不存在"
}
```

**响应体（已订阅）：**

```json
{
  "code": 40002,
  "message": "已订阅该番剧"
}
```

**错误码：**

| 错误码 | 含义 |
|--------|------|
| 40401 | 番剧不存在 |
| 40002 | 已订阅该番剧 |

---

## 4. 取消订阅番剧

用户取消对指定番剧的订阅。

| 项目 | 内容 |
|------|------|
| 方法 | DELETE |
| 路径 | `/api/anime/subscribe/{anime_id}` |
| 认证 | 需要（Bearer Token） |

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| anime_id | string | 番剧ID |

**请求体：** 无

**响应体（成功）：**

```json
{
  "code": 0,
  "message": "success",
  "data": { "success": true }
}
```

> 已取消的番剧再次取消仍返回成功，不会报错。

---

## 5. 获取网盘链接 & 催更

用户点击复制网盘链接时调用：返回百度/夸克网盘链接，同时标记用户需要此番剧的更新提醒。

| 项目 | 内容 |
|------|------|
| 方法 | POST |
| 路径 | `/api/anime/get-link-and-remind` |
| 认证 | 需要（Bearer Token） |
| Content-Type | application/json |

**请求体：**

```json
{
  "anime_id": "abc123",
  "current_episode": "更至36集"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| anime_id | string | 是 | 番剧ID |
| current_episode | string | 否 | 用户当前看到的集数，用于催更比对 |

**响应体（成功）：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "baidu_url": "https://pan.baidu.com/s/xxx",
    "baidu_password": "abcd",
    "quark_url": "https://pan.quark.cn/s/yyy",
    "is_reminded": true
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| baidu_url | string | 百度网盘链接 |
| baidu_password | string | 百度网盘提取码 |
| quark_url | string | 夸克网盘链接 |
| is_reminded | boolean | 催更是否成功 |

**响应体（番剧不存在）：**

```json
{
  "code": 40401,
  "message": "番剧不存在"
}
```

**业务说明：**

- 每次调用会记录一次催更标记，后台可据此判断哪些用户需要推送更新通知
- 如果番剧有更新（episode 变化），可向 `is_reminded=true` 的用户发送订阅消息提醒
- `current_episode` 记录用户当前看到的集数，用于判断增量推送

---

## 6. 附录

### 6.1 通用响应格式

所有接口统一返回：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | 0=成功，其他=错误 |
| message | string | 提示信息 |
| data | object | 业务数据 |

### 6.2 通用错误码

| 错误码 | 含义 |
|--------|------|
| 0 | 成功 |
| 40101 | 未登录或 Token 无效 |
| 50001 | 服务器内部错误 |

### 6.3 业务错误码（本模块专用）

| 错误码 | 含义 | 触发接口 |
|--------|------|----------|
| 40009 | 番剧不存在 | 订阅 / 取链 |
| 40010 | 已订阅该番剧 | 订阅 |

### 6.4 资源类型枚举

| type 值 | 说明 |
|---------|------|
| `anime` | 番剧（默认） |
| `movie` | 电影 |
| `4k` | 4K 资源 |

### 6.5 接入示例（JavaScript / 小程序）

```javascript
// 1. 获取番剧列表
const res = await fetch('https://your-api.com/api/anime/library?type=anime&page=1&page_size=10', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const { data } = await res.json();
console.log(data.list);       // 番剧列表
console.log(data.total);      // 总数

// 2. 订阅番剧
await fetch('https://your-api.com/api/anime/subscribe', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ anime_id: 'abc123' })
});

// 3. 获取网盘链接
const linkRes = await fetch('https://your-api.com/api/anime/get-link-and-remind', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ anime_id: 'abc123' })
});
const linkData = await linkRes.json();
wx.setClipboardData({ data: `链接:${linkData.data.baidu_url} 提取码:${linkData.data.baidu_password}` });
```

### 6.6 关注点

| 场景 | 建议 |
|------|------|
| 列表分页 | 使用 `total / page_size` 计算总页数，递归加载 |
| 重复订阅 | 捕获 `code=40002`，前端静默处理（toast 提示即可） |
| Token 过期 | 捕获 `code=40101`，重新走微信登录流程 |
| 网盘链接 | 获取链接后触发 `setClipboardData` 复制 |
| 催更 | 获取链接即为催更，无需额外操作 |