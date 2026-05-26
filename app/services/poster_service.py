import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.badge_service import get_badge_by_id
from app.services.poster_pro import (
    generate_gaming_badge_poster,
    generate_spotify_wrapped_monthly,
)
from app.services.stats_service import get_user_stats

logger = logging.getLogger(__name__)


async def generate_monthly_poster(
    db: AsyncSession,
    user_id: UUID,
) -> str:
    """
    Generate Spotify Wrapped style monthly statistics poster
    
    Features:
    - Dark gradient background (Spotify style)
    - Bold typography with year badge
    - Progress bars for each stat
    - 7-day activity bar chart
    - Professional gaming/modern aesthetic
    """
    logger.info(f"Generating PRO Spotify-style monthly poster for user: {user_id}")
    
    stats = await get_user_stats(db, user_id, "month")
    logger.debug(f"Stats data received: {stats}")
    
    result = generate_spotify_wrapped_monthly(stats)
    logger.info("PRO monthly poster generated and saved to output/posters/")
    return result


async def generate_badge_poster(
    db: AsyncSession,
    user_id: UUID,
    badge_id: str,
) -> str:
    """
    Generate Gaming Achievement style badge poster
    
    Features:
    - Dark space/gaming theme
    - Glowing circle effect around badge
    - "Achievement Unlocked" header
    - Rarity tier colors (Common/Rare/Epic/Legendary)
    - XP/Coins reward decoration
    """
    logger.info(f"Generating PRO Gaming-style badge poster for user: {user_id}, badge_id: {badge_id}")
    
    badge = await get_badge_by_id(db, badge_id, user_id)
    logger.debug(f"Badge data received: {badge}")
    
    result = generate_gaming_badge_poster(badge if badge else {})
    logger.info("PRO badge poster generated and saved to output/posters/")
    return result
