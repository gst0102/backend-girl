# 项目开发进度

## 技术栈
- 语言：Python 3.10
- 框架：FastAPI
- 数据库：PostgreSQL 15+
- ORM：SQLAlchemy 2.0+
- 架构：MVC
- 包管理：uv

## 已完成（数据库表）

✅ **已完成：users, invite_relations, records, user_features, badges, user_badges, guardian_relations, couple_relations, families, family_members, push_logs, reward_logs, config_unlock, config_push_templates**

| 表名 | SQL 文件 | Model 文件 | 状态 |
| :--- | :--- | :--- | :--- |
| users | `app/sql/schema.sql` | `app/models/user.py` | ✅ 已建表 |
| invite_relations | `app/sql/schema.sql` | `app/models/user.py` | ✅ 已建表 |
| records | `app/sql/schema.sql` | `app/models/user.py` | ✅ 已建表 |
| user_features | `app/sql/schema.sql` | `app/models/feature.py` | ✅ 已建表 |
| badges | `app/sql/schema.sql` | `app/models/badge.py` | ✅ 已建表 |
| user_badges | `app/sql/schema.sql` | `app/models/badge.py` | ✅ 已建表 |
| guardian_relations | `app/sql/schema.sql` | `app/models/guardian.py` | ✅ 已建表 |
| couple_relations | `app/sql/schema.sql` | `app/models/couple.py` | ✅ 已建表 |
| families | `app/sql/schema.sql` | `app/models/family.py` | ✅ 已建表 |
| family_members | `app/sql/schema.sql` | `app/models/family.py` | ✅ 已建表 |
| push_logs | `app/sql/schema.sql` | `app/models/push.py` | ✅ 已建表 |
| reward_logs | `app/sql/schema.sql` | `app/models/reward.py` | ✅ 已建表 |
| config_unlock | `app/sql/schema.sql` | `app/models/config.py` | ✅ 已建表 |
| config_push_templates | `app/sql/schema.sql` | `app/models/config.py` | ✅ 已建表 |

- [x] users
- [x] invite_relations
- [x] records
- [x] user_features
- [x] badges
- [x] user_badges
- [x] guardian_relations
- [x] couple_relations
- [x] families
- [x] family_members
- [x] push_logs
- [x] reward_logs
- [x] config_unlock
- [x] config_push_templates

## 已完成（框架搭建）
- [x] requirements.txt
- [x] app/config.py - 配置管理
- [x] app/database.py - 异步数据库引擎
- [x] app/main.py - FastAPI 入口
- [x] app/models/base.py - DeclarativeBase
- [x] app/schemas/response.py - 统一响应模型
- [x] app/schemas/user.py - 用户 Pydantic 模型
- [x] app/controllers/user_controller.py - 用户路由
- [x] app/services/user_service.py - 用户业务逻辑
- [x] app/middleware/auth.py - JWT 认证中间件

## 已完成（API 接口）
- [ ] POST /api/user/login
- [ ] GET /api/user/info
- [ ] POST /api/record/create
- [ ] GET /api/calendar
- [ ] GET /api/today/status
- [ ] POST /api/invite/create
- [ ] GET /api/invite/progress
- [ ] GET /api/rank/list
- [ ] POST /api/guardian/create
- [ ] POST /api/guardian/confirm
- [ ] POST /api/couple/create
- [ ] GET /api/couple/info
- [ ] GET /api/family/info
- [ ] POST /api/family/join
- [ ] GET /api/badge/list
- [ ] GET /api/stats
- [ ] POST /api/poster/generate

## 待开发
- [ ] 用户认证中间件
- [ ] 邀请解锁逻辑
- [ ] 推送服务
- [ ] 定时任务
- [ ] 限流中间件

## 最后更新
2026-05-18