from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import os
import uuid

from app.database import get_db
from app.dependencies import get_current_user_id
from app.schemas.response import CodeEnum, error_json, success_response
from app.schemas.user import LoginRequest, LoginResponse
from app.services.auth_service import (
    BASE_FEATURES,
    create_jwt_token,
    create_new_user,
    get_user_by_id,
    get_user_by_openid,
)
from app.services.badge_service import get_user_badges
from app.services.invite_service import create_invite_relation
from app.services.wechat_service import get_wx_openid

router = APIRouter()

UPLOAD_DIR = "static/avatars"


class UpdateNicknameRequest(BaseModel):
    nickname: str


@router.post("/user/nickname")
async def update_nickname(
    req: UpdateNicknameRequest,
    current_user_id = Depends(get_current_user_id),  # 不要写类型，让它自动推断
    db: AsyncSession = Depends(get_db)
):
    if len(req.nickname) < 1 or len(req.nickname) > 20:
        return error_json(CodeEnum.PARAM_ERROR, "昵称长度应为1-20字符")
    
    # 直接传，不转换
    user = await get_user_by_id(db, current_user_id)
    if not user:
        return error_json(CodeEnum.USER_NOT_FOUND)
    
    user.nickname = req.nickname
    await db.commit()
    await db.refresh(user)
    
    return success_response(data={"nickname": user.nickname})


@router.post("/user/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    # 强制转成字符串
    user_id_str = str(user_id)
    # 确保目录存在
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    if isinstance(user_id, UUID):
        uid = user_id
    else:
        uid = UUID(user_id)
    
    user = await get_user_by_id(db, user_id)
    if not user:
        return error_json(CodeEnum.USER_NOT_FOUND)
    
    # 生成唯一文件名
    ext = file.filename.split('.')[-1] if '.' in file.filename else 'png'
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # 保存文件
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    
    # ✅ 修复：用 user 变量
    avatar_url = f"/static/avatars/{filename}"
    user.avatar = avatar_url
    await db.commit()
    
    return success_response(data={"avatar_url": avatar_url})


@router.post("/user/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    openid = await get_wx_openid(req.code)
    user = await get_user_by_openid(db, openid)
    is_new = user is None
    
    if is_new:
        user = await create_new_user(db, openid)
        await db.flush()
        if req.inviter_id:
            try:
                new_count = await create_invite_relation(db, UUID(req.inviter_id), user.openid)
                from app.services.invite_service import check_and_unlock_features
                await check_and_unlock_features(db, UUID(req.inviter_id), new_count)
                from app.services.badge_service import check_and_award_all
                await check_and_award_all(db, UUID(req.inviter_id), "invite")
            except ValueError:
                pass
    
    await db.commit()
    await db.refresh(user)
    
    token = create_jwt_token(str(user.id))
    return success_response(
        data=LoginResponse(
            user_id=str(user.id),
            is_new=is_new,
            invite_count=user.invite_count,
            unlocked_features=BASE_FEATURES,
            token=token,
        ).model_dump()
    )

@router.get("/user/info")
async def user_info(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_id(db, user_id)
    if user is None:
        return error_json(CodeEnum.USER_NOT_FOUND)

    from app.models.feature import UserFeature
    from sqlalchemy import select
    feature_result = await db.execute(
        select(UserFeature).where(UserFeature.user_id == user.id)
    )
    unlocked_features = [f.feature_key for f in feature_result.scalars().all()]

    badges = await get_user_badges(db, user.id)

    return success_response(data={
        "user_id": str(user.id),
        "nickname": user.nickname,
        "avatar": user.avatar,
        "invite_count": user.invite_count,
        "continuous_days": user.continuous_days,
        "unlocked_features": unlocked_features,
        "badges": badges,
    })


@router.post("/user/logout")
async def logout(
    user_id: str = Depends(get_current_user_id),
):
    """用户登出 - 清除服务端状态（当前为无状态JWT，直接返回成功）"""
    return success_response(data=None)