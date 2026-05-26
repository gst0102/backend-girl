from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user_id
from app.schemas.response import success_response
from app.services.stats_service import get_user_stats
from datetime import date, timedelta
from typing import Optional
from uuid import UUID
from collections import defaultdict
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.dependencies import get_current_user_id
from app.models.record import Record
from app.models.user import User
from app.schemas.response import success_response, error_json, CodeEnum

router = APIRouter(prefix="/stats")


# @router.get("")
# async def stats(
#     period: str = Query("month", description="month / last_month / all"),
#     user_id: str = Depends(get_current_user_id),
#     db: AsyncSession = Depends(get_db),
# ):
#     data = await get_user_stats(db, UUID(user_id), period)
#     trend = data.pop("trend", [])
#     return success_response(data={
#         "overview": data,
#         "trend": trend,
#     })



# app/routers/stats.py





# app/routers/stats.py

from datetime import date, timedelta
from typing import Optional
from uuid import UUID
from collections import defaultdict
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.dependencies import get_current_user_id
from app.models.record import Record
from app.models.user import User
from app.schemas.response import success_response, error_json, CodeEnum

router = APIRouter(prefix="/stats", tags=["统计"])


@router.get("")
async def get_user_stats(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    period: str = Query("month", description="month/last_month/all"),
    target_user_id: Optional[str] = Query(None, description="被守护者用户ID"),
):
    """
    获取用户统计数据
    一个接口搞定所有：概览卡片、类型统计、趋势图、环形图
    """
    
    # 权限检查：如果查看他人数据，需校验守护权限
    if target_user_id and target_user_id != user_id:
        from app.services.guardian_service import check_guardian_permission
        has_perm = await check_guardian_permission(
            db, UUID(user_id), UUID(target_user_id), "stats"
        )
        if not has_perm:
            return error_json(CodeEnum.FORBIDDEN, "无权限查看该用户的统计数据")
        user_id = target_user_id
    
    # ========== 1. 计算日期范围 ==========
    today = date.today()
    start_date = None
    end_date = None
    
    if period == "month":
        start_date = date(today.year, today.month, 1)
        # 下个月第一天
        if today.month == 12:
            end_date = date(today.year + 1, 1, 1)
        else:
            end_date = date(today.year, today.month + 1, 1)
    elif period == "last_month":
        if today.month == 1:
            start_date = date(today.year - 1, 12, 1)
            end_date = date(today.year, 1, 1)
        else:
            start_date = date(today.year, today.month - 1, 1)
            end_date = date(today.year, today.month, 1)
    # else: period == "all" -> start_date/end_date 为 None，查询所有
    
    # ========== 2. 查询当前用户的记录（按日期范围） ==========
    query = select(Record).where(Record.user_id == UUID(user_id))
    if start_date:
        query = query.where(Record.record_date >= start_date)
    if end_date:
        query = query.where(Record.record_date < end_date)
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    # ========== 3. 初始化数据结构 ==========
    # 所有14种记录类型
    all_types = [
        "poop", "period", "sleep", "water",
        "anime", "exercise", "study", "habit",
        "medicine", "mood", "cold", "pet",
        "love", "weight"
    ]
    
    # 类型显示信息
    type_info = {
        "poop": {"name": "拉屎", "icon": "💩"},
        "period": {"name": "姨妈", "icon": "🩸"},
        "sleep": {"name": "睡眠", "icon": "😴"},
        "water": {"name": "喝水", "icon": "💧"},
        "anime": {"name": "追番", "icon": "📺"},
        "exercise": {"name": "运动", "icon": "🏋️"},
        "study": {"name": "学习", "icon": "📚"},
        "habit": {"name": "习惯", "icon": "✅"},
        "medicine": {"name": "吃药", "icon": "💊"},
        "mood": {"name": "心情", "icon": "😊"},
        "cold": {"name": "感冒", "icon": "🤧"},
        "pet": {"name": "宠物", "icon": "🐾"},
        "love": {"name": "恋爱", "icon": "💕"},
        "weight": {"name": "体重", "icon": "⚖️"},
    }
    
    # 类型统计
    type_stats = {t: 0 for t in all_types}
    
    # 睡眠评分列表
    sleep_scores = []
    
    # 每日记录数（用于趋势图）
    daily_count = defaultdict(int)
    
    # 所有有记录的日期集合（用于计算连续天数）
    record_dates = set()
    
    # 各类型次数（用于环形图）
    distribution = defaultdict(int)
    
    # ========== 4. 遍历记录，收集数据 ==========
    for r in records:
        # 类型统计
        if r.record_type in type_stats:
            type_stats[r.record_type] += 1
        
        # 分布统计
        distribution[r.record_type] += 1
        
        # 每日记录数
        daily_count[r.record_date] += 1
        
        # 记录日期（用于连续天数）
        record_dates.add(r.record_date)
        
        # 睡眠评分
        if r.record_type == "sleep" and r.record_value:
            # 兼容 score 和 quality 字段
            score = r.record_value.get("score") or r.record_value.get("quality")
            if score:
                # 如果是 1-5 星，转换为百分制
                if score <= 5:
                    score = score * 20
                sleep_scores.append(score)
    
    # ========== 5. 计算概览卡片数据 ==========
    
    # 5.1 拉屎次数
    poop_count = type_stats["poop"]
    
    # 5.2 睡眠均分
    sleep_avg_score = round(sum(sleep_scores) / len(sleep_scores)) if sleep_scores else 0
    
    # 5.3 连续记录天数（从今天往前推）
    continuous_days = 0
    check_date = today
    while check_date in record_dates:
        continuous_days += 1
        check_date -= timedelta(days=1)
    
    # 5.4 击败用户百分比
    # 查询所有用户的记录总数
    all_users_query = select(
        Record.user_id, 
        func.count(Record.id).label("total_count")
    ).group_by(Record.user_id)
    all_users_result = await db.execute(all_users_query)
    all_users_stats = all_users_result.all()
    
    current_user_total = len(records)
    less_count = 0
    for _, total in all_users_stats:
        if total < current_user_total:
            less_count += 1
    
    total_users = len(all_users_stats)
    beat_users_percent = round(less_count / total_users * 100) if total_users > 0 else 0
    
    overview = {
        "poop_count": poop_count,
        "sleep_avg_score": sleep_avg_score,
        "continuous_days": continuous_days,
        "beat_users_percent": beat_users_percent,
    }
    
    # ========== 6. 构建类型统计列表 ==========
    type_stats_list = []
    for t in all_types:
        count = type_stats[t]
        type_stats_list.append({
            "type": t,
            "name": type_info[t]["name"],
            "icon": type_info[t]["icon"],
            "count": count,
            "has_record": count > 0,
            "display_count": str(count) if count > 0 else "-",
        })
    
    # ========== 7. 趋势图数据（近7天） ==========
    weekdays = ["一", "二", "三", "四", "五", "六", "日"]
    trend = []
    
    # 找到最大值用于计算高度百分比
    max_count = 1
    for i in range(7):
        d = today - timedelta(days=6 - i)
        count = daily_count.get(d, 0)
        if count > max_count:
            max_count = count
    
    for i in range(7):
        d = today - timedelta(days=6 - i)
        count = daily_count.get(d, 0)
        height_percent = round(count / max_count * 100) if max_count > 0 else 0
        trend.append({
            "day": weekdays[i],
            "date": d.isoformat(),
            "count": count,
            "height_percent": height_percent,
        })
    
    # ========== 8. 环形图数据 ==========
    # 取前4个类型 + 其他
    sorted_types = sorted(distribution.items(), key=lambda x: x[1], reverse=True)
    top_4 = sorted_types[:4]
    other_count = sum(count for _, count in sorted_types[4:])
    
    # 颜色配置
    colors = ["#5a8f3c", "#85c1e9", "#f4d03f", "#f5b7b1", "#bcaaa4"]
    type_names = {
        "poop": "拉屎", "sleep": "睡眠", "water": "喝水", 
        "mood": "心情", "exercise": "运动", "habit": "习惯",
        "anime": "追番", "pet": "宠物", "love": "恋爱",
        "period": "姨妈", "study": "学习", "medicine": "吃药",
        "cold": "感冒", "weight": "体重"
    }
    
    circumference = 440  # 圆周长 2 * π * 70 ≈ 440
    current_offset = 0
    distribution_items = []
    
    for idx, (type_name, count) in enumerate(top_4):
        total = sum(distribution.values())
        percentage = count / total if total > 0 else 0
        dash_array = percentage * circumference
        distribution_items.append({
            "type": type_name,
            "name": type_names.get(type_name, type_name),
            "count": count,
            "percentage": round(percentage * 100),
            "color": colors[idx],
            "stroke_dasharray": dash_array,
            "stroke_dashoffset": -current_offset,
        })
        current_offset += dash_array
    
    # 添加"其他"
    if other_count > 0:
        total = sum(distribution.values())
        percentage = other_count / total if total > 0 else 0
        dash_array = percentage * circumference
        distribution_items.append({
            "type": "other",
            "name": "其他",
            "count": other_count,
            "percentage": round(percentage * 100),
            "color": colors[4],
            "stroke_dasharray": dash_array,
            "stroke_dashoffset": -current_offset,
        })
    
    # ========== 9. 返回完整数据 ==========
    return success_response(data={
        "period": period,
        "overview": overview,
        "type_stats": type_stats_list,
        "trend": trend,
        "distribution": {
            "total": sum(distribution.values()),
            "items": distribution_items,
        },
        "total_records": len(records),
    })