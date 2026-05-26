import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine


async def seed_animes():
    async with engine.begin() as conn:
        # 插入番剧数据 (anime)
        await conn.execute(text("""
            INSERT INTO animes (id, title, quality, episode, status, baidu_url, baidu_password, quark_url, update_time, type, created_at, updated_at) VALUES 
            ('anime_001', '歌手 2026', '1080P', '更5.23', NULL, 'https://pan.baidu.com/s/fake_singer', '1234', 'https://pan.quark.cn/s/fake_singer', '05-24', 'anime', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            ('anime_002', '咒术回战 第三季', '1080P', '更08', '连载中', 'https://pan.baidu.com/s/jujutsu', 'abcd', 'https://pan.quark.cn/s/jujutsu', '05-23', 'anime', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            ('anime_003', '鬼灭之刃 柱训练篇', '1080P', '更03', '连载中', 'https://pan.baidu.com/s/demon_slayer', '5678', 'https://pan.quark.cn/s/demon_slayer', '05-22', 'anime', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            ('anime_004', '葬送的芙莉莲', '1080P', '完结', '已完结', 'https://pan.baidu.com/s/frieren', '1122', 'https://pan.quark.cn/s/frieren', '05-20', 'anime', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO NOTHING
        """))
        
        # 插入电影数据 (movie)
        await conn.execute(text("""
            INSERT INTO animes (id, title, quality, episode, status, baidu_url, baidu_password, quark_url, update_time, type, created_at, updated_at) VALUES 
            ('movie_001', '流浪地球3', '1080P', '正片', '已上映', 'https://pan.baidu.com/s/wandering_earth', '3344', 'https://pan.quark.cn/s/wandering_earth', '02-12', 'movie', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            ('movie_002', '哪吒之魔童闹海', '1080P', '正片', '已上映', 'https://pan.baidu.com/s/nezha', '5566', 'https://pan.quark.cn/s/nezha', '01-29', 'movie', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            ('movie_003', '封神2', '1080P', '正片', '已上映', 'https://pan.baidu.com/s/fengshen', '7788', 'https://pan.quark.cn/s/fengshen', '12-15', 'movie', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO NOTHING
        """))
        
        # 插入4K影视数据 (anime_4k)
        await conn.execute(text("""
            INSERT INTO animes (id, title, quality, episode, status, baidu_url, baidu_password, quark_url, update_time, type, created_at, updated_at) VALUES 
            ('4k_001', '阿凡达3', '4K', '正片', '已上映', 'https://pan.baidu.com/s/avatar', '9900', 'https://pan.quark.cn/s/avatar', '03-15', 'anime_4k', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            ('4k_002', '盗梦空间', '4K', '正片', '经典', 'https://pan.baidu.com/s/inception', 'aabb', 'https://pan.quark.cn/s/inception', '04-01', 'anime_4k', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            ('4k_003', '星际穿越', '4K', '正片', '经典', 'https://pan.baidu.com/s/interstellar', 'ccdd', 'https://pan.quark.cn/s/interstellar', '04-10', 'anime_4k', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO NOTHING
        """))
        
    print("[OK] Seed data inserted: animes (3 types: anime/movie/anime_4k)")


async def main():
    await seed_animes()


if __name__ == "__main__":
    asyncio.run(main())
