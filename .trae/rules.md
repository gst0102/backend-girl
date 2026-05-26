# 项目规范

## 技术栈
- 前端：UniApp + Vue3 + TypeScript + Pinia
- 后端：Python 3.10 + FastAPI + PostgreSQL + SQLAlchemy

## 一、后端规范

### 响应格式
```python
class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: Optional[T] = None
错误码
0: 成功

40001-40008: 业务错误（参数/用户/记录/功能/邀请等）

40101: 未登录

50001: 服务器错误

接口路径
基础路径：/api

示例：POST /api/user/login、GET /api/calendar

二、前端规范
技术栈约束
框架：UniApp + Vue3

语言：TypeScript

状态管理：Pinia

API 服务层规范（重要！）
统一使用 services/request.ts 封装

❌ 禁止在组件中直接调用 uni.request

❌ 禁止硬编码 URL

UniApp 请求规范（关键！）
uni.request 不支持 params 参数

GET 请求参数必须手动拼接到 URL

✅ 正确：url: '/api/calendar?year=2026&month=5'

❌ 错误：params: { year, month }

命名规范
文件名：kebab-case

函数名：camelCase + Api 后缀（如 getUserInfoApi）

类型/接口名：PascalCase

三、接口路径表（常用）
接口	方法	路径
登录	POST	/user/login
用户信息	GET	/user/info
日历	GET	/calendar?year=&month=
今日状态	GET	/today/status
创建记录	POST	/record/create
邀请进度	GET	/invite/progress
排行榜	GET	/rank/list
四、禁止事项
❌ 禁止在前端使用 params 字段

❌ 禁止在组件中直接调用 uni.request

❌ 禁止后端硬编码 URL

❌ 禁止跳过统一响应格式