import asyncio
import json
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine


def parse_title(title):
    """解析标题，提取主要信息"""
    # 提取画质
    quality = "1080P"
    if "4K" in title:
        quality = "4K"
    elif "1080P" in title:
        quality = "1080P"
    elif "720P" in title:
        quality = "720P"
    
    # 提取更新状态
    episode = ""
    # 匹配 "更X.Y" 或 "更X" 或 "更XY.Z" 等格式
    update_match = re.search(r'更(\d+\.?\d*)[期集]?', title)
    if update_match:
        episode = f"更{update_match.group(1)}"
    else:
        # 匹配 "X集全" 或 "X.Y集全"
        full_match = re.search(r'(\d+\.?\d*)[期集]全', title)
        if full_match:
            episode = f"{full_match.group(1)}集全"
    
    # 提取状态标签
    status = None
    if "完结" in title:
        status = "已完结"
    elif "超前" in title:
        status = "超前点播"
    elif "铂金" in title or "高码" in title:
        status = "珍藏版"
    
    # 清理标题 - 去掉画质、更新信息、标签等
    clean_title = title
    patterns_to_remove = [
        r'\.1080P', r'1080P', r'720P', r'4K',
        r'更\d+\.?\d*[期集]?', r'\d+\.?\d*[期集]全',
        r'【超前完结】', r'【完结】', r'【新】',
        r'（\d+\.?\d*[期集]全）', r'\(\d+\.?\d*[期集]全\)',
        r'（1080P\.?.*?\）', r'\(1080P\.?.*?\)',
        r'（铂金珍藏版）', r'\(铂金珍藏版\)',
        r'（官方正式版\)', r'\(官方正式版\)',
        r'（高码）', r'\(高码\)',
    ]
    
    for pattern in patterns_to_remove:
        clean_title = re.sub(pattern, '', clean_title)
    
    # 再做一些清理
    clean_title = re.sub(r'\s+', ' ', clean_title).strip()
    clean_title = re.sub(r'^[\.\s]+|[\.\s]+$', '', clean_title)
    
    # 提取更新时间
    update_time = "05-24"  # 默认值
    time_match = re.search(r'(\d+)\.(\d+)', title)
    if time_match:
        month = time_match.group(1).zfill(2)
        day = time_match.group(2).zfill(2)
        if int(month) <= 12:
            update_time = f"{month}-{day}"
    
    return {
        "title": clean_title,
        "quality": quality,
        "episode": episode,
        "status": status,
        "update_time": update_time
    }


async def import_from_json(json_path, media_type):
    """从JSON文件导入数据"""
    print(f"\n正在导入 {json_path} (类型: {media_type})...")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    entries = data.get('entries', [])
    print(f"  共 {len(entries)} 条数据")
    
    success_count = 0
    
    for i, entry in enumerate(entries):
        title = entry.get('title', '')
        
        # 解析标题信息
        parsed = parse_title(title)
        
        # 提取链接
        baidu_url = ""
        baidu_password = "1120"
        quark_url = ""
        
        for link in entry.get('links', []):
            if link.get('type') == '百度网盘':
                baidu_url = link.get('url', '')
                if 'extract_code' in link:
                    baidu_password = link.get('extract_code', '1120')
            elif link.get('type') == '夸克网盘':
                quark_url = link.get('url', '')
        
        # 生成ID
        # 从标题生成简短ID，避免太长
        clean_id = re.sub(r'[^\w\u4e00-\u9fa5]', '', parsed['title'])[:20]
        anime_id = f"{media_type}_{i}_{clean_id}"
        # 确保ID不太长
        if len(anime_id) > 50:
            anime_id = f"{media_type}_{i}"
        
        try:
            async with engine.begin() as conn:
                # 检查是否已存在
                result = await conn.execute(
                    text("SELECT 1 FROM animes WHERE id = :id"),
                    {"id": anime_id}
                )
                exists = result.scalar()
                
                if not exists:
                    await conn.execute(text("""
                        INSERT INTO animes (
                            id, title, quality, episode, status, 
                            baidu_url, baidu_password, quark_url, 
                            update_time, type, created_at, updated_at
                        ) VALUES (
                            :id, :title, :quality, :episode, :status,
                            :baidu_url, :baidu_password, :quark_url,
                            :update_time, :type, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                        )
                    """), {
                        "id": anime_id,
                        "title": parsed['title'],
                        "quality": parsed['quality'],
                        "episode": parsed['episode'],
                        "status": parsed['status'],
                        "baidu_url": baidu_url,
                        "baidu_password": baidu_password,
                        "quark_url": quark_url,
                        "update_time": parsed['update_time'],
                        "type": media_type
                    })
                    success_count += 1
                    if success_count % 20 == 0:
                        print(f"  已导入 {success_count} 条...")
        except Exception as e:
            print(f"  导入第 {i} 条时出错: {e}")
    
    print(f"  成功导入 {success_count} 条 {media_type} 数据!")


async def clear_data():
    """清空旧数据"""
    print("正在清空旧数据...")
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM user_anime_subscriptions"))
        await conn.execute(text("DELETE FROM anime_reminders"))
        await conn.execute(text("DELETE FROM animes"))
    print("旧数据已清空!")


async def main():
    print("=" * 60)
    print("开始导入真实影视数据")
    print("=" * 60)
    
    # 先清空数据
    await clear_data()
    
    # 三个JSON文件
    base_path = Path(__file__).parent.parent / "date"
    
    files = [
        ("影视剧.json", "anime"),
        ("电影.json", "movie"),
        ("4K.json", "anime_4k")
    ]
    
    # 导入每个文件
    for filename, media_type in files:
        full_path = base_path / filename
        if full_path.exists():
            await import_from_json(full_path, media_type)
        else:
            print(f"警告: 文件 {filename} 不存在!")
    
    # 统计数据
    print("\n" + "=" * 60)
    print("数据统计")
    print("=" * 60)
    
    async with engine.begin() as conn:
        for media_type in ["anime", "movie", "anime_4k"]:
            result = await conn.execute(
                text("SELECT COUNT(*) FROM animes WHERE type = :type"),
                {"type": media_type}
            )
            count = result.scalar()
            print(f"  {media_type}: {count} 条")
        
        total_result = await conn.execute(text("SELECT COUNT(*) FROM animes"))
        total = total_result.scalar()
        print(f"\n  总计: {total} 条数据")
    
    print("\n数据导入完成！")


if __name__ == "__main__":
    asyncio.run(main())
