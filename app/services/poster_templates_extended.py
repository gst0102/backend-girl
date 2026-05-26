import io
import logging
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)
OUTPUT_DIR = Path("output/posters")


def create_xiaohongshu_monthly(stats: dict) -> str:
    """
    小红书风格月度报告海报
    
    特点：
    - 粉嫩渐变背景
    - 圆角卡片设计
    - 可爱字体和图标
    - 小红书标志性风格
    """
    logger.info("Creating Xiaohongshu style monthly poster...")
    
    width, height = 600, 900
    img = Image.new("RGB", (width, height), "#FFE4E9")
    draw = ImageDraw.Draw(img)
    
    # 添加装饰元素
    import random
    for _ in range(20):
        cx = random.randint(0, width)
        cy = random.randint(0, height)
        cr = random.randint(10, 30)
        draw.ellipse([cx-cr, cy-cr, cx+cr, cy+cr], fill=(255, 182, 193, 50))
    
    # 标题区域
    title_font = ImageFont.truetype("arial.ttf", 36)
    subtitle_font = ImageFont.truetype("arial.ttf", 18)
    
    draw.text((30, 40), "📝 我的月度报告", fill="#FF69B4", font=title_font)
    draw.text((30, 90), f"{date.today().strftime('%Y年%m月')}", fill="#FF69B4", font=subtitle_font)
    
    # 统计卡片
    cards_y = 140
    card_height = 100
    card_spacing = 20
    
    stats_list = [
        ("💩", "拉屎次数", f"{stats.get('poop_count', 0)}次", "#FF6B6B"),
        ("😴", "睡眠分数", f"{stats.get('sleep_score', 0)}分", "#4ECDC4"),
        ("🔥", "连续记录", f"{stats.get('continuous_days', 0)}天", "#FFA726"),
        ("🏆", "击败用户", f"{stats.get('beat_users', 0)}%", "#66BB6A"),
    ]
    
    icon_font = ImageFont.truetype("arial.ttf", 32)
    label_font = ImageFont.truetype("arial.ttf", 16)
    value_font = ImageFont.truetype("arial.ttf", 24)
    
    for i, (icon, label, value, color) in enumerate(stats_list):
        cy = cards_y + i * (card_height + card_spacing)
        
        draw.rounded_rectangle((30, cy, 570, cy + card_height), 20, fill="white")
        
        draw.text((50, cy + 35), icon, font=icon_font)
        draw.text((120, cy + 25), label, fill="#666", font=label_font)
        draw.text((120, cy + 55), value, fill=color, font=value_font)
    
    # 底部装饰
    draw.text((280, height - 40), "💕 记录美好生活", fill="#FFB6C1", font=subtitle_font)
    
    filename = f"xiaohongshu_monthly_{date.today().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = OUTPUT_DIR / filename
    img.save(filepath, "PNG")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return __import__("base64").b64encode(buffer.getvalue()).decode("utf-8")


def create_cute_cartoon_monthly(stats: dict) -> str:
    """
    卡通手绘风格月度报告
    
    特点：
    - 可爱的卡通元素
    - 手绘风格边框
    - 活泼的配色
    - 气泡对话框设计
    """
    logger.info("Creating cute cartoon style monthly poster...")
    
    width, height = 600, 950
    img = Image.new("RGB", (width, height), "#FFF8E7")
    draw = ImageDraw.Draw(img)
    
    # 手绘波浪边框
    for i in range(0, width, 20):
        draw.arc([i, 0, i+15, 15], 0, 180, fill="#FFE4B5", width=3)
        draw.arc([i, height-15, i+15, height], 180, 360, fill="#FFE4B5", width=3)
    
    # 标题气泡
    draw.ellipse([50, 30, 130, 110], fill="#FFB6C1")
    draw.ellipse([45, 95, 70, 120], fill="#FFB6C1")
    draw.text((65, 55), "Hi~", fill="white", font=ImageFont.truetype("arial.ttf", 24))
    
    title_font = ImageFont.truetype("arial.ttf", 32)
    draw.text((150, 60), "我的健康日记", fill="#FF69B4", font=title_font)
    
    # 卡通统计卡片
    cards = [
        {"icon": "💩", "label": "便便次数", "value": f"{stats.get('poop_count', 0)}次", "bg": "#FFF5EE"},
        {"icon": "🛏️", "label": "睡眠质量", "value": f"{stats.get('sleep_score', 0)}分", "bg": "#E0FFE0"},
        {"icon": "🔥", "label": "连续打卡", "value": f"{stats.get('continuous_days', 0)}天", "bg": "#FFF5E0"},
    ]
    
    y = 160
    for card in cards:
        draw.rounded_rectangle((40, y, 560, y + 120), 25, fill=card["bg"])
        
        # 云朵装饰
        draw.ellipse([50, y+10, 100, y+40], fill="#FFB6C1")
        draw.ellipse([80, y+5, 130, y+35], fill="#FFB6C1")
        
        draw.text((150, y+45), card["icon"], font=ImageFont.truetype("arial.ttf", 40))
        draw.text((230, y+35), card["label"], fill="#666", font=ImageFont.truetype("arial.ttf", 20))
        draw.text((230, y+75), card["value"], fill="#FF69B4", font=ImageFont.truetype("arial.ttf", 32))
        
        y += 140
    
    # 底部装饰文字
    draw.text((200, height-60), "✨ 坚持就是胜利 ✨", fill="#FFA500", font=ImageFont.truetype("arial.ttf", 20))
    
    filename = f"cartoon_monthly_{date.today().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = OUTPUT_DIR / filename
    img.save(filepath, "PNG")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return __import__("base64").b64encode(buffer.getvalue()).decode("utf-8")


def create_minimal_japanese_monthly(stats: dict) -> str:
    """
    简约日系风格月度报告
    
    特点：
    - 清新淡雅配色
    - 极简设计
    - 留白艺术
    - 日式美学
    """
    logger.info("Creating minimal Japanese style monthly poster...")
    
    width, height = 600, 850
    img = Image.new("RGB", (width, height), "#FAFAFA")
    draw = ImageDraw.Draw(img)
    
    # 极简标题
    title_font = ImageFont.truetype("arial.ttf", 28)
    draw.text((30, 50), "Monthly", fill="#333", font=title_font)
    draw.text((30, 85), "Health Report", fill="#666", font=ImageFont.truetype("arial.ttf", 18))
    
    # 日期
    draw.text((450, 50), date.today().strftime("%Y.%m.%d"), fill="#999", font=ImageFont.truetype("arial.ttf", 16))
    
    # 分隔线
    draw.line([(30, 130), (570, 130)], fill="#E0E0E0", width=1)
    
    # 极简统计卡片
    stats_data = [
        ("Poops", str(stats.get("poop_count", 0))),
        ("Sleep", f"{stats.get('sleep_score', 0)}%"),
        ("Streak", f"{stats.get('continuous_days', 0)} days"),
        ("Rank", f"Top {stats.get('beat_users', 0)}%"),
    ]
    
    y = 160
    for label, value in stats_data:
        draw.text((30, y), label, fill="#999", font=ImageFont.truetype("arial.ttf", 14))
        draw.text((150, y-5), value, fill="#333", font=ImageFont.truetype("arial.ttf", 28))
        draw.line([(30, y+30), (570, y+30)], fill="#F0F0F0", width=1)
        y += 55
    
    # 趋势区域
    draw.text((30, y+20), "Weekly Trend", fill="#999", font=ImageFont.truetype("arial.ttf", 14))
    
    trend = stats.get("trend", [2, 3, 1, 4, 3, 5, 2])
    max_val = max(trend) if trend else 1
    bar_width = 60
    gap = 15
    start_x = 30
    
    for i, val in enumerate(trend):
        bar_height = int((val / max_val) * 80)
        x = start_x + i * (bar_width + gap)
        draw.rectangle([x, y+100-bar_height, x+bar_width, y+100], fill="#E8F5E9")
        
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        draw.text((x+5, y+115), day_names[i], fill="#BBB", font=ImageFont.truetype("arial.ttf", 10))
    
    # 底部签名
    draw.text((30, height-50), "Girl Backend", fill="#DDD", font=ImageFont.truetype("arial.ttf", 12))
    
    filename = f"japanese_monthly_{date.today().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = OUTPUT_DIR / filename
    img.save(filepath, "PNG")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return __import__("base64").b64encode(buffer.getvalue()).decode("utf-8")


def create_vintage_newspaper_monthly(stats: dict) -> str:
    """
    复古报纸风格月度报告
    
    特点：
    - 报纸排版风格
    - 复古纸张质感
    - 打字机字体效果
    - 新闻标题风格
    """
    logger.info("Creating vintage newspaper style monthly poster...")
    
    width, height = 600, 900
    img = Image.new("RGB", (width, height), "#F5E6D3")
    draw = ImageDraw.Draw(img)
    
    # 添加纸张纹理
    pixels = img.load()
    for _ in range(10000):
        import random
        x = random.randint(0, width-1)
        y = random.randint(0, height-1)
        noise = random.randint(-5, 5)
        r, g, b = pixels[x, y]
        pixels[x, y] = (max(240, min(255, r+noise)), 
                        max(220, min(255, g+noise)), 
                        max(200, min(255, b+noise)))
    
    # 报纸标题
    title_font = ImageFont.truetype("arial.ttf", 20)
    draw.text((30, 30), "THE GIRL TIMES", fill="#8B4513", font=title_font)
    draw.text((30, 55), "HEALTH EDITION", fill="#A0522D", font=ImageFont.truetype("arial.ttf", 14))
    
    # 日期线
    draw.line([(30, 80), (570, 80)], fill="#D2691E", width=2)
    draw.text((30, 90), f"Date: {date.today().strftime('%B %d, %Y')}", fill="#8B4513", font=ImageFont.truetype("arial.ttf", 12))
    
    # 大字标题
    headline_font = ImageFont.truetype("arial.ttf", 32)
    draw.text((30, 130), "RECORDS SHOW", fill="#8B4513", font=headline_font)
    draw.text((30, 170), "HEALTH PROGRESS", fill="#8B4513", font=headline_font)
    
    # 统计数据（报纸风格）
    y = 230
    stats_list = [
        ("Poop Count", f"{stats.get('poop_count', 0)} times this month"),
        ("Sleep Score", f"{stats.get('sleep_score', 0)} out of 100"),
        ("Streak Record", f"{stats.get('continuous_days', 0)} consecutive days"),
        ("Community Rank", f"Top {stats.get('beat_users', 0)}% of users"),
    ]
    
    for label, value in stats_list:
        draw.text((30, y), label, fill="#5D4037", font=ImageFont.truetype("arial.ttf", 16))
        draw.text((30, y+25), value, fill="#8B4513", font=ImageFont.truetype("arial.ttf", 20))
        draw.line([(30, y+55), (570, y+55)], fill="#DEB887", width=1)
        y += 75
    
    # 装饰元素
    draw.text((30, y+20), "***", fill="#D2691E", font=ImageFont.truetype("arial.ttf", 16))
    
    filename = f"vintage_monthly_{date.today().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = OUTPUT_DIR / filename
    img.save(filepath, "PNG")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return __import__("base64").b64encode(buffer.getvalue()).decode("utf-8")


TEMPLATE_MAP = {
    "xiaohongshu": {
        "name": "小红书风格",
        "function": create_xiaohongshu_monthly,
        "description": "粉嫩可爱，适合分享到小红书"
    },
    "cartoon": {
        "name": "卡通手绘风", 
        "function": create_cute_cartoon_monthly,
        "description": "活泼可爱的卡通风格"
    },
    "japanese": {
        "name": "简约日系",
        "function": create_minimal_japanese_monthly,
        "description": "清新淡雅，日式极简美学"
    },
    "vintage": {
        "name": "复古报纸",
        "function": create_vintage_newspaper_monthly, 
        "description": "复古报纸排版风格"
    },
}


def get_available_templates():
    """获取所有可用模板列表"""
    return [
        {"key": key, "name": info["name"], "description": info["description"]}
        for key, info in TEMPLATE_MAP.items()
    ]


def generate_with_template(template_key: str, stats: dict) -> str:
    """使用指定模板生成海报"""
    if template_key not in TEMPLATE_MAP:
        raise ValueError(f"Unknown template: {template_key}")
    
    return TEMPLATE_MAP[template_key]["function"](stats)
