# 技术设计文档 - 徽章系统、数据统计和海报生成

## 版本：V1.0 | 更新日期：2026年5月
---

## 一、需求分析

### 1.1 需求来源
根据 `需求.md` 和 `产品需求文档（PRD）.md`，本次需要实现以下功能：

| 模块 | 功能 | 优先级 |
|------|------|--------|
| 徽章系统 | 徽章触发、查询、展示 | P2 |
| 数据统计 | 月度统计、趋势分析、击败率计算 | P2 |
| 海报生成 | 月度战绩、情侣同步率、徽章炫耀海报 | P2 |

### 1.2 业务流程

```
┌─────────────────────────────────────────────────────────────┐
│                      徽章触发流程                           │
├─────────────────────────────────────────────────────────────┤
│  创建记录 → 更新连续天数 → check_and_award_badges()        │
│         → 插入 user_badges → 插入 reward_logs              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      统计计算流程                           │
├─────────────────────────────────────────────────────────────┤
│  GET /api/stats → get_user_stats() → 查询记录 + 排名计算   │
│         → 计算趋势 → 返回统计数据                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      海报生成流程                           │
├─────────────────────────────────────────────────────────────┤
│  POST /api/poster/generate → 获取数据 → Pillow绘图         │
│         → 转换Base64 → 返回图片数据                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、架构设计

### 2.1 模块划分

| 模块 | 文件 | 职责 |
|------|------|------|
| 徽章服务 | `app/services/badge_service.py` | 徽章触发、查询、状态管理 |
| 统计服务 | `app/services/stats_service.py` | 用户数据统计、趋势分析 |
| 海报服务 | `app/services/poster_service.py` | 图片生成、Base64编码 |
| 徽章控制器 | `app/controllers/badge_controller.py` | 徽章相关API路由 |
| 统计控制器 | `app/controllers/stats_controller.py` | 统计相关API路由 |
| 海报控制器 | `app/controllers/poster_controller.py` | 海报生成API路由 |
| 数据模型 | `app/schemas/badge.py` | 徽章数据结构 |
| 数据模型 | `app/schemas/stats.py` | 统计数据结构 |
| 数据模型 | `app/schemas/poster.py` | 海报请求/响应结构 |

### 2.2 核心类与方法设计

#### 2.2.1 BadgeService

| 方法名 | 功能说明 | 参数 | 返回值 |
|--------|----------|------|--------|
| `check_and_award_badges` | 检查并颁发徽章 | `user_id`, `trigger_type`, `trigger_value` | `list[dict]` |
| `get_user_badges` | 获取用户已获得徽章 | `user_id` | `list[dict]` |
| `get_all_badges_with_status` | 获取所有徽章及用户拥有状态 | `user_id` | `dict` |
| `get_badge_by_id` | 根据ID查询徽章 | `badge_id`, `user_id` | `dict` |

#### 2.2.2 StatsService

| 方法名 | 功能说明 | 参数 | 返回值 |
|--------|----------|------|--------|
| `get_user_stats` | 获取用户统计数据 | `user_id`, `period` | `dict` |
| `get_poop_trend` | 获取拉屎趋势 | `user_id`, `days` | `list[int]` |
| `get_sleep_score_stats` | 获取睡眠分数统计 | `user_id`, `period` | `int` |

#### 2.2.3 PosterService

| 方法名 | 功能说明 | 参数 | 返回值 |
|--------|----------|------|--------|
| `generate_monthly_poster` | 生成月度海报 | `user_id` | `str(base64)` |
| `generate_couple_poster` | 生成情侣海报 | `user_id` | `str(base64)` |
| `generate_badge_poster` | 生成徽章海报 | `user_id`, `badge_id` | `str(base64)` |

---

## 三、数据库与数据结构设计

### 3.1 数据库表结构（已有）

#### badges 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(20) | 徽章ID |
| name | VARCHAR(30) | 徽章名称 |
| icon | VARCHAR(10) | 图标(emoji) |
| rarity | VARCHAR(10) | 稀有度(common/rare/epic) |
| condition_type | VARCHAR(30) | 条件类型 |
| condition_value | INT | 条件值 |

#### user_badges 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| user_id | UUID | 用户ID |
| badge_id | VARCHAR(20) | 徽章ID |
| earned_at | TIMESTAMPTZ | 获得时间 |

### 3.2 API 请求/响应结构

#### 3.2.1 徽章接口

**GET /api/badge/list**

响应结构：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 10,
    "owned": 3,
    "owned_badges": [
      {"id": "badge_001", "name": "连续拉屎7天", "icon": "💩", "rarity": "rare", "earned_at": "2026-05-10"}
    ],
    "locked_badges": [
      {"id": "badge_002", "name": "裂变之王", "icon": "🏆", "rarity": "epic", "condition": "邀请10人解锁"}
    ]
  }
}
```

#### 3.2.2 统计接口

**GET /api/stats?period=month**

响应结构：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "poop_count": 17,
    "sleep_score": 81,
    "continuous_days": 7,
    "beat_percent": 92,
    "trend": [4, 7, 5, 8, 3, 6, 5]
  }
}
```

#### 3.2.3 海报接口

**POST /api/poster/generate**

请求结构：
```json
{
  "template": "monthly",
  "badge_id": null
}
```

响应结构：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "image_base64": "data:image/png;base64,iVBORw0KGgo..."
  }
}
```

---

## 四、API 接口设计

### 4.1 徽章控制器

| API路径 | HTTP方法 | 功能 | 认证 |
|---------|----------|------|------|
| `/api/badge/list` | GET | 获取徽章列表（含拥有状态） | 需要 |
| `/api/badge/detail/{badge_id}` | GET | 获取徽章详情 | 需要 |

### 4.2 统计控制器

| API路径 | HTTP方法 | 功能 | 认证 |
|---------|----------|------|------|
| `/api/stats` | GET | 获取用户统计数据 | 需要 |

### 4.3 海报控制器

| API路径 | HTTP方法 | 功能 | 认证 |
|---------|----------|------|------|
| `/api/poster/generate` | POST | 生成海报 | 需要 |
| `/api/poster/templates` | GET | 获取可用模板列表 | 需要 |

---

## 五、主业务流程与调用链

### 5.1 徽章触发流程

```
record_service.create_record()
    │
    ├─→ 更新连续天数
    │
    └─→ badge_service.check_and_award_badges(
            user_id,
            trigger_type="continuous_days",
            trigger_value=new_continuous_days
        )
            │
            ├─→ 查询 badges 表（符合条件的徽章）
            │
            ├─→ 查询 user_badges 表（用户已获得的徽章）
            │
            ├─→ 计算差集（未获得的徽章）
            │
            ├─→ 批量插入 user_badges
            │
            └─→ 批量插入 reward_logs
```

### 5.2 统计数据计算流程

```
GET /api/stats
    │
    └─→ stats_controller.stats()
            │
            └─→ stats_service.get_user_stats(user_id, period)
                    │
                    ├─→ 查询 Record 表（poop_count）
                    │
                    ├─→ 查询 Record 表（sleep_score 平均值）
                    │
                    ├─→ 查询 User 表（continuous_days）
                    │
                    ├─→ 计算 beat_percent（窗口函数排名）
                    │
                    └─→ 计算 trend（最近7天每天的记录数）
```

### 5.3 海报生成流程

```
POST /api/poster/generate
    │
    └─→ poster_controller.poster_generate()
            │
            ├─→ 根据 template 类型调用对应方法
            │
            ├─→ stats_service.get_user_stats() / couple_service.get_couple_info()
            │
            └─→ pillow 绘图 → base64 编码 → 返回
```

---

## 六、部署与集成方案

### 6.1 依赖说明

| 依赖 | 版本 | 用途 |
|------|------|------|
| Pillow | >=10.0.0 | 图片生成 |
| SQLAlchemy | >=2.0 | 数据库ORM |
| asyncpg | >=0.27 | PostgreSQL异步驱动 |

### 6.2 配置与运行

```bash
# 安装依赖
pip install -e .

# 启动服务
uvicorn app.main:app --reload --port 8000

# 数据库初始化（首次运行）
python -m app.init_db
```

---

## 七、代码安全性

### 7.1 注意事项

| 风险点 | 描述 | 关联模块 |
|--------|------|----------|
| SQL注入 | 动态查询可能存在注入风险 | badge_service, stats_service |
| 越权访问 | 用户可能访问他人数据 | 所有控制器 |
| 资源耗尽 | 海报生成可能消耗大量内存 | poster_service |
| Base64注入 | 恶意base64数据可能导致问题 | poster_controller |

### 7.2 解决方案

| 风险点 | 解决方案 |
|--------|----------|
| SQL注入 | 使用 SQLAlchemy 参数化查询 |
| 越权访问 | 所有接口使用 JWT 认证，校验用户权限 |
| 资源耗尽 | 限制图片尺寸（600x800），添加请求限流 |
| Base64注入 | 对返回的base64数据进行长度限制和格式验证 |

---

## 八、测试计划

### 8.1 测试文件结构

```
test/
├── __init__.py
├── api-test.py          # API接口测试
├── flow-test.py         # 业务流程测试
├── anime-test.py        # 番剧模块测试
├── seed_animes.py       # 番剧数据初始化
└── seed_animes.sql      # 番剧SQL脚本
```

### 8.2 测试用例覆盖

| 模块 | 测试点 |
|------|--------|
| 徽章服务 | 徽章触发、查询、状态判断 |
| 统计服务 | 不同周期统计、趋势计算、击败率 |
| 海报服务 | 三种模板生成、base64格式验证 |
| 接口测试 | 认证、参数校验、错误处理 |

---

## 九、输出文件清单

| 文件路径 | 状态 | 说明 |
|----------|------|------|
| `app/services/badge_service.py` | ✅ | 徽章服务实现 |
| `app/services/stats_service.py` | ✅ | 统计服务实现 |
| `app/services/poster_service.py` | ✅ | 海报服务实现 |
| `app/schemas/badge.py` | ✅ | 徽章数据模型 |
| `app/schemas/stats.py` | ✅ | 统计数据模型 |
| `app/schemas/poster.py` | ✅ | 海报数据模型 |
| `app/controllers/badge_controller.py` | ✅ | 徽章控制器 |
| `app/controllers/stats_controller.py` | ✅ | 统计控制器 |
| `app/controllers/poster_controller.py` | ✅ | 海报控制器 |
| `app/controllers/__init__.py` | ✅ | 路由注册 |
| `test/api-test.py` | ✅ | API测试脚本 |
| `test/flow-test.py` | ✅ | 流程测试脚本 |
| `test/anime-test.py` | ✅ | 番剧测试脚本 |

---

*文档结束*
