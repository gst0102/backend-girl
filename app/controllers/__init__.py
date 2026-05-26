from fastapi import APIRouter

from app.controllers import (
    ad_controller,
    admin_controller,
    anime_controller,
    badge_controller,
    config_controller,
    invite_controller,
    poster_controller,
    record_controller,
    stats_controller,
    user_controller,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(user_controller.router)
api_router.include_router(record_controller.router)
api_router.include_router(invite_controller.router)
api_router.include_router(invite_controller.rank_router)
api_router.include_router(badge_controller.router, tags=["徽章"])
api_router.include_router(stats_controller.router, tags=["统计"])
api_router.include_router(poster_controller.router, tags=["海报"])
api_router.include_router(anime_controller.router, tags=["追番"])
api_router.include_router(config_controller.router, tags=["配置"])
api_router.include_router(config_controller.feedback_router, tags=["反馈"])
api_router.include_router(config_controller.upload_router, tags=["配置"])
api_router.include_router(config_controller.marquee_router, tags=["跑马灯"])
api_router.include_router(ad_controller.router, tags=["广告"])
api_router.include_router(admin_controller.router, tags=["管理后台"])