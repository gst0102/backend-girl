from datetime import date
from typing import Optional
from uuid import UUID
from app.models.record import Record 
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.dependencies import get_current_user_id, get_current_user_id_optional
from app.models.user import User
from app.schemas.record import (
    RecordCreateRequest,
    CalendarResponse,
    DayInfo,
    FeatureStatus,
)
from app.schemas.response import CodeEnum, error_json, success_response
from app.services.record_service import (
    calculate_continuous_days,
    check_badges,
    create_record,
    get_calendar_data,
    get_today_status,
)

router = APIRouter()


@router.post("/record/create")
async def create_record_endpoint(
    req: RecordCreateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    print("=" * 50)
    print(f"收到请求: {req}")
    print(f"record_type: {req.record_type}, record_date: {req.record_date}, record_value: {req.record_value}")
    print("=" * 50)
    try:
        record_date = date.fromisoformat(req.record_date)
    except ValueError:
        return error_json(CodeEnum.PARAM_ERROR, "日期格式错误，应为 yyyy-mm-dd")

    try:
        record_id, continuous_days = await create_record(
            db, UUID(user_id), req.record_type, record_date, req.record_value
        )
    except ValueError as e:
        error_map = {
            "FEATURE_LOCKED": (CodeEnum.FEATURE_LOCKED, f"功能 [{req.record_type}] 尚未解锁"),
            "RECORD_EXISTS": (CodeEnum.RECORD_EXISTS, "今日该类型已记录"),
        }
        code, detail = error_map.get(str(e), (CodeEnum.SERVER_ERROR, str(e)))
        return error_json(code, detail)

    badges_earned = await check_badges(db, UUID(user_id), continuous_days)

    await db.commit()
    return success_response(data={
        "record_id": record_id,
        "continuous_days": continuous_days,
        "badges_earned": badges_earned,
    })


@router.get("/calendar")
async def calendar(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user_id: Optional[str] = Depends(get_current_user_id_optional),
    db: AsyncSession = Depends(get_db),
):
    # 未登录：返回公开日历数据（仅红点，所有用户汇总）
    if not current_user_id:
        today = date.today()
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        result = await db.execute(
            select(Record.record_date).distinct().where(
                Record.record_date >= start_date,
                Record.record_date < end_date,
            )
        )
        record_dates = {row[0].day for row in result.all()}
        return success_response(data={
            "year": year,
            "month": month,
            "today": today.day if today.year == year and today.month == month else 0,
            "record_days": sorted(record_dates),
            "days": [],
            "records_map": {},
        })

    data = await get_calendar_data(db, UUID(current_user_id), year, month)
    return success_response(data=data)


@router.get("/today/status")
async def get_today_status_endpoint(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    from app.services.record_service import get_today_status
    features_data = await get_today_status(db, UUID(current_user_id))
    return success_response(data=features_data)


@router.get("/today/records")
async def get_today_records(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取今日所有记录（支持多组）"""
    today = date.today()
    
    result = await db.execute(
        select(Record).where(
            Record.user_id == UUID(current_user_id),
            Record.record_date == today,
        ).order_by(Record.created_at)
    )
    records = result.scalars().all()
    
    data = {}
    for r in records:
        if r.record_type not in data:
            data[r.record_type] = []
        data[r.record_type].append({
            "id": r.id,
            "record_type": r.record_type,
            "record_value": r.record_value,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    
    return success_response(data=data)


# 获取指定日期记录
@router.get("/records")
async def get_records_by_date(
    date_str: str = Query(..., description="日期 yyyy-mm-dd"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取指定日期的所有记录"""
    try:
        record_date = date.fromisoformat(date_str)
    except ValueError:
        return error_json(CodeEnum.PARAM_ERROR, "日期格式错误，应为 yyyy-mm-dd")
    
    result = await db.execute(
        select(Record).where(
            Record.user_id == UUID(current_user_id),
            Record.record_date == record_date,
        )
    )
    records = result.scalars().all()
    
    data = []
    for r in records:
        data.append({
            "record_type": r.record_type,
            "record_value": r.record_value,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    
    return success_response(data=data)
