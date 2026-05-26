import io
import logging
import math
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("output/posters")


def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color string to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


class ProfessionalPosterEngine:
    """Professional poster template engine with modern design"""
    
    def __init__(self, width: int = 600, height: int = 1000):
        self.width = width
        self.height = height
        self.img = None
        self.draw = None
    
    def _get_font(self, size: int, bold: bool = False):
        """Get font with fallback"""
        fonts = ["arialbd.ttf"] if bold else ["arial.ttf"]
        for font_name in fonts:
            try:
                return ImageFont.truetype(font_name, size)
            except Exception:
                continue
        return ImageFont.load_default()
    
    def _parse_color(self, color) -> tuple:
        """Parse color to RGB tuple (supports both hex string and tuple)"""
        if isinstance(color, str):
            return hex_to_rgb(color)
        return color
    
    def create_gradient_bg(self, color_top: tuple, color_bottom: tuple) -> Image.Image:
        """Create smooth gradient background with noise texture"""
        img = Image.new("RGB", (self.width, self.height))
        draw = ImageDraw.Draw(img)
        
        r1, g1, b1 = color_top
        r2, g2, b2 = color_bottom
        
        for y in range(self.height):
            ratio = y / self.height
            # Use ease-in-out for smoother gradient
            ratio_smooth = ratio * ratio * (3 - 2 * ratio)
            r = int(r1 + (r2 - r1) * ratio_smooth)
            g = int(g1 + (g2 - g1) * ratio_smooth)
            b = int(b1 + (b2 - b1) * ratio_smooth)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b))
        
        # Add subtle noise for texture
        import random
        pixels = img.load()
        for i in range(50000):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            current = pixels[x, y]
            noise = random.randint(-8, 8)
            new_color = tuple(max(0, min(255, c + noise)) for c in current)
            pixels[x, y] = new_color
        
        return img
    
    def draw_rounded_rect(self, xy, radius: int, fill=None, outline=None, shadow=False):
        """Draw rounded rectangle with optional shadow"""
        if shadow:
            shadow_offset = 4
            shadow_xy = (xy[0] + shadow_offset, xy[1] + shadow_offset,
                        xy[2] + shadow_offset, xy[3] + shadow_offset)
            self.draw_rounded_rect(shadow_xy, radius, fill=(0, 0, 0, 30))
        
        x1, y1, x2, y2 = xy
        if fill:
            # Main rectangle parts
            self.draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
            self.draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
            # Corner circles
            self.draw.pieslice([x1, y1, x1 + 2*radius, y1 + 2*radius], 180, 270, fill=fill)
            self.draw.pieslice([x2 - 2*radius, y1, x2, y1 + 2*radius], 270, 360, fill=fill)
            self.draw.pieslice([x1, y2 - 2*radius, x1 + 2*radius, y2], 90, 180, fill=fill)
            self.draw.pieslice([x2 - 2*radius, y2 - 2*radius, x2, y2], 0, 90, fill=fill)
    
    def draw_progress_bar(self, xy, percentage: float, bg_color: str, fg_color: str, height: int = 12):
        """Draw a modern progress bar with rounded ends"""
        x1, y1, x2, y2 = xy
        bar_height = height
        
        # Background bar
        self.draw.rounded_rectangle(
            [x1, y1, x2, y1 + bar_height],
            radius=bar_height // 2,
            fill=bg_color
        )
        
        # Foreground bar (filled portion)
        filled_width = int((x2 - x1) * min(percentage / 100, 1))
        if filled_width > 0:
            self.draw.rounded_rectangle(
                [x1, y1, x1 + filled_width, y1 + bar_height],
                radius=bar_height // 2,
                fill=fg_color
            )
    
    def draw_stat_card(self, xy, icon: str, label: str, value: str, 
                       accent_color: str, show_progress=False, progress_val=0):
        """Draw a beautiful stat card with icon and progress"""
        x1, y1, x2, y2 = xy
        card_height = y2 - y1
        padding = 20
        
        # Parse color to RGB tuple
        rgb_color = self._parse_color(accent_color)
        
        # Card background with shadow effect
        self.draw_rounded_rect((x1+3, y1+3, x2+3, y2+3), 16, fill=(0, 0, 0, 20))
        self.draw_rounded_rect((x1, y1, x2, y2), 16, fill="white")
        
        # Left accent stripe
        self.draw.rectangle([x1, y1+10, x1+5, y2-10], fill=rgb_color)
        
        # Icon circle (semi-transparent version)
        icon_size = 44
        icon_x = x1 + padding + 15
        icon_y = y1 + (card_height - icon_size) // 2
        
        # Create semi-transparent color by blending with white
        semi_transparent = tuple(int(c * 0.7) for c in rgb_color)
        self.draw.ellipse(
            [icon_x, icon_y, icon_x + icon_size, icon_y + icon_size],
            fill=semi_transparent
        )
        
        # Icon text
        icon_font = self._get_font(22)
        icon_text_bbox = self.draw.textbbox((0, 0), icon, font=icon_font)
        icon_w = icon_text_bbox[2] - icon_text_bbox[0]
        icon_h = icon_text_bbox[3] - icon_text_bbox[1]
        self.draw.text(
            (icon_x + (icon_size - icon_w) // 2, icon_y + (icon_size - icon_h) // 2),
            icon, fill="white", font=icon_font
        )
        
        # Label and Value
        text_x = icon_x + icon_size + 20
        label_font = self._get_font(14)
        value_font = self._get_font(26, bold=True)
        
        self.draw.text((text_x, y1 + 28), label, fill=(120, 120, 120), font=label_font)
        self.draw.text((text_x, y1 + 52), value, fill=rgb_color, font=value_font)
        
        # Progress bar (optional)
        if show_progress:
            progress_y = y2 - 25
            self.draw_progress_bar(
                (text_x, progress_y, x2 - padding, progress_y + 8),
                progress_val, "#f0f0f0", rgb_color, 8
            )


def generate_spotify_wrapped_monthly(stats: dict) -> str:
    """
    Generate Spotify Wrapped style monthly poster
    
    Features:
    - Dark gradient background
    - Bold typography
    - Animated-style stat cards
    - Progress bars and visualizations
    """
    logger.info("Generating Spotify Wrapped style monthly poster...")
    
    engine = ProfessionalPosterEngine(width=600, height=1100)
    
    # Dark gradient background (like Spotify)
    engine.img = engine.create_gradient_bg(
        color_top=(25, 25, 35),
        color_bottom=(45, 30, 60)
    )
    engine.draw = ImageDraw.Draw(engine.img)
    
    # Header section - Big bold title
    title_font = engine._get_font(48, bold=True)
    subtitle_font = engine._get_font(20)
    
    # Year badge
    year = date.today().year
    year_font = engine._get_font(80, bold=True)
    engine.draw.text((40, 50), str(year), fill=(29, 185, 84), font=year_font)
    
    engine.draw.text((40, 150), "YOUR MONTHLY", fill="white", font=title_font)
    engine.draw.text((40, 210), "HEALTH STORY", fill=(29, 185, 84), font=title_font)
    
    engine.draw.text((40, 290), f"Period: {date.today().strftime('%B %Y')}", 
                     fill=(150, 150, 150), font=subtitle_font)
    
    # Stats section
    card_y = 350
    card_spacing = 110
    card_height = 95
    
    stats_data = [
        ("\u26a0\ufe0f", "Poop Count", f"{stats.get('poop_count', 0)} times", "#FF6B6B", True, 75),
        ("\u2604\ufe0f", "Sleep Score", f"{stats.get('sleep_score', 0)} pts", "#4ECDC4", True, 85),
        ("\U0001f525", "Streak Days", f"{stats.get('continuous_days', 0)} days", "#FFA726", True, 60),
        ("\U0001f3c6", "Beat Users", f"{stats.get('beat_users', 0)}%", "#66BB6A", True, 78),
    ]
    
    for i, (icon, label, value, color, show_prog, prog_val) in enumerate(stats_data):
        cy = card_y + i * (card_height + card_spacing // 2)
        engine.draw_stat_card(
            (30, cy, 570, cy + card_height),
            icon, label, value, color, show_prog, prog_val
        )
    
    # Trend visualization (simple bar chart)
    trend_y = card_y + len(stats_data) * (card_height + card_spacing // 2) + 30
    engine.draw_rounded_rect((30, trend_y, 570, trend_y + 200), 20, fill=(255, 255, 255, 10))
    
    trend_title_font = engine._get_font(18, bold=True)
    engine.draw.text((50, trend_y + 15), "7-Day Activity Trend", fill="white", font=trend_title_font)
    
    trend_values = stats.get("trend", [3, 5, 2, 7, 4, 6, 8])
    max_val = max(trend_values) if trend_values else 1
    bar_width = 50
    bar_spacing = 70
    start_x = 80
    base_y = trend_y + 170
    
    for i, val in enumerate(trend_values):
        bar_height = int((val / max_val) * 100)
        x = start_x + i * bar_spacing
        y = base_y - bar_height
        
        # Bar gradient effect (darker at bottom)
        bar_color = (29, 185, 84)
        engine.draw.rectangle([x, y, x + bar_width, base_y], fill=bar_color)
        
        # Value on top of bar
        val_font = engine._get_font(14, bold=True)
        val_text = str(val)
        val_bbox = engine.draw.textbbox((0, 0), val_text, font=val_font)
        val_w = val_bbox[2] - val_bbox[0]
        engine.draw.text((x + (bar_width - val_w)//2, y - 20), val_text, fill="white", font=val_font)
    
    # Footer
    footer_font = engine._get_font(12)
    engine.draw.text((300, engine.height - 40), 
                     "\u25cf Generated by Girl Backend \u25cf",
                     fill=(100, 100, 100), font=footer_font)
    
    # Save to file
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = date.today().strftime("%Y%m%d_%H%M%S")
    filename = f"spotify_monthly_{timestamp}.png"
    filepath = OUTPUT_DIR / filename
    
    engine.img.save(filepath, "PNG", quality=95)
    logger.info(f"Spotify-style monthly poster saved to: {filepath}")
    
    # Convert to base64
    buffer = io.BytesIO()
    engine.img.save(buffer, format="PNG")
    import base64
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def generate_instagram_couple_poster(info: dict) -> str:
    """
    Generate Instagram-style couple sync poster
    
    Features:
    - Soft pastel gradients
    - Heart-themed design
    - Modern card layout
    - Relationship metrics
    """
    logger.info("Generating Instagram-style couple poster...")
    
    engine = ProfessionalPosterEngine(width=600, height=900)
    
    # Romantic pink-purple gradient
    engine.img = engine.create_gradient_bg(
        color_top=(255, 107, 140),
        color_bottom=(147, 112, 219)
    )
    engine.draw = ImageDraw.Draw(engine.img)
    
    # Decorative circles (bokeh effect)
    for _ in range(15):
        import random
        cx = random.randint(0, engine.width)
        cy = random.randint(0, engine.height)
        cr = random.randint(20, 60)
        alpha = random.randint(10, 30)
        engine.draw.ellipse([cx-cr, cy-cr, cx+cr, cy+cr], 
                          fill=(255, 255, 255, alpha))
    
    # Main content card (white, centered)
    card_margin = 30
    card_top = 80
    card_bottom = engine.height - 80
    engine.draw_rounded_rect(
        (card_margin, card_top, engine.width - card_margin, card_bottom),
        24, fill="white"
    )
    
    # Title with heart
    title_font = engine._get_font(36, bold=True)
    subtitle_font = engine._get_font(18)
    
    title_text = "Couple Sync Report"
    title_bbox = engine.draw.textbbox((0, 0), title_text, font=title_font)
    title_w = title_bbox[2] - title_bbox[0]
    engine.draw.text(
        ((engine.width - title_w) // 2, card_top + 40),
        title_text, fill=(255, 107, 140), font=title_font
    )
    
    subtitle_text = "Your Relationship Health Dashboard"
    sub_bbox = engine.draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
    sub_w = sub_bbox[2] - sub_bbox[0]
    engine.draw.text(
        ((engine.width - sub_w) // 2, card_top + 90),
        subtitle_text, fill=(150, 150, 150), font=subtitle_font
    )
    
    # Divider line
    line_y = card_top + 130
    engine.draw.line([(card_margin + 50, line_y), (engine.width - card_margin - 50, line_y)], 
                     fill=(240, 240, 240), width=2)
    
    # Stats grid (2x2)
    sync_rate = info.get("sync_rate", 0) if info else 0
    bind_days = info.get("bind_days", 0) if info else 0
    common = info.get("common_days", 0) if info else 0
    overlap = info.get("period_overlap", 0) if info else 0
    
    grid_data = [
        ("Sync Rate", f"{sync_rate}%", "\u2764\ufe0f", "#FF6B9D"),
        ("Together For", f"{bind_days} days", "\u2665", "#FF69B4"),
        ("Shared Records", f"{common} days", "\U0001f49e", "#DDA0DD"),
        ("Cycle Sync", f"{overlap} days", "\u2648", "#FFB6C1"),
    ]
    
    grid_start_y = card_top + 160
    card_padding = 50
    inner_card_w = (engine.width - 2 * card_margin - 3 * 20) // 2
    inner_card_h = 140
    
    for idx, (label, value, icon, color) in enumerate(grid_data):
        row = idx // 2
        col = idx % 2
        
        ix = card_margin + card_padding + col * (inner_card_w + 20)
        iy = grid_start_y + row * (inner_card_h + 20)
        
        # Inner card
        engine.draw_rounded_rect(
            (ix, iy, ix + inner_card_w, iy + inner_card_h),
            16, fill="#FAFAFA"
        )
        
        # Icon
        icon_font = engine._get_font(32)
        icon_text = icon
        icon_bbox = engine.draw.textbbox((0, 0), icon_text, font=icon_font)
        icon_w = icon_bbox[2] - icon_bbox[0]
        engine.draw.text(
            (ix + (inner_card_w - icon_w) // 2, iy + 20),
            icon_text, fill=color, font=icon_font
        )
        
        # Label
        label_font = engine._get_font(14)
        label_bbox = engine.draw.textbbox((0, 0), label, font=label_font)
        label_w = label_bbox[2] - label_bbox[0]
        engine.draw.text(
            (ix + (inner_card_w - label_w) // 2, iy + 70),
            label, fill=(120, 120, 120), font=label_font
        )
        
        # Value
        value_font = engine._get_font(24, bold=True)
        value_bbox = engine.draw.textbbox((0, 0), value, font=value_font)
        value_w = value_bbox[2] - value_bbox[0]
        engine.draw.text(
            (ix + (inner_card_w - value_w) // 2, iy + 98),
            value, fill=color, font=value_font
        )
    
    # Love meter (progress bar style)
    meter_y = grid_start_y + 2 * (inner_card_h + 20) + 30
    meter_label_font = engine._get_font(16, bold=True)
    meter_label = "Love Sync Meter"
    meter_label_bbox = engine.draw.textbbox((0, 0), meter_label, font=meter_label_font)
    meter_label_w = meter_label_bbox[2] - meter_label_bbox[0]
    engine.draw.text(
        ((engine.width - meter_label_w) // 2, meter_y),
        meter_label, fill=(80, 80, 80), font=meter_label_font
    )
    
    # Progress bar
    bar_y = meter_y + 35
    bar_margin = card_margin + 60
    engine.draw_progress_bar(
        (bar_margin, bar_y, engine.width - bar_margin, bar_y + 14),
        sync_rate, "#FFE4E9", "#FF6B9D", 14
    )
    
    # Percentage text
    pct_font = engine._get_font(14, bold=True)
    pct_text = f"{sync_rate}%"
    pct_bbox = engine.draw.textbbox((0, 0), pct_text, font=pct_font)
    pct_w = pct_bbox[2] - pct_bbox[0]
    engine.draw.text(
        ((engine.width - pct_w) // 2, bar_y + 22),
        pct_text, fill=(255, 107, 157), font=pct_font
    )
    
    # Save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = date.today().strftime("%Y%m%d_%H%M%S")
    filename = f"instagram_couple_{timestamp}.png"
    filepath = OUTPUT_DIR / filename
    
    engine.img.save(filepath, "PNG", quality=95)
    logger.info(f"Instagram-style couple poster saved to: {filepath}")
    
    buffer = io.BytesIO()
    engine.img.save(buffer, format="PNG")
    import base64
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def generate_gaming_badge_poster(badge: dict) -> str:
    """
    Generate gaming achievement style badge poster
    
    Features:
    - Dark gaming theme
    - Glowing effects
    - Achievement unlocked animation style
    - Rarity tiers with colors
    """
    logger.info("Generating gaming achievement style badge poster...")
    
    engine = ProfessionalPosterEngine(width=600, height=800)
    
    # Dark space/gaming gradient
    engine.img = engine.create_gradient_bg(
        color_top=(15, 15, 25),
        color_bottom=(30, 20, 40)
    )
    engine.draw = ImageDraw.Draw(engine.img)
    
    # Star/sparkle decorations
    import random
    for _ in range(30):
        sx = random.randint(0, engine.width)
        sy = random.randint(0, engine.height)
        ss = random.randint(1, 3)
        sa = random.randint(100, 255)
        engine.draw.rectangle([sx, sy, sx+ss, sy+ss], fill=(sa, sa, sa))
    
    # Badge name
    name = badge.get("name", "Mystery Badge") or "Mystery Badge"
    rarity = badge.get("rarity", "Common") or "Common"
    icon = badge.get("icon", "\U0001f3c6") or "\U0001f3c6"
    earned_at = badge.get("earned_at", "") or ""
    
    # Rarity colors (gaming style)
    rarity_colors = {
        "Common": ((169, 169, 169), "#AAAAAA", "\u26aa"),      # Gray
        "Rare": ((65, 105, 225), "#4169E1", "\U0001f535"),     # Blue
        "Epic": ((148, 0, 211), "#9400D3", "\U0001f7e2"),       # Purple
        "Legendary": ((255, 165, 0), "#FFA500", "\U0001f31f"),   # Gold
    }
    main_color, hex_color, rarity_icon = rarity_colors.get(rarity, rarity_colors["Common"])
    
    # Achievement Unlocked header
    header_font = engine._get_font(24)
    header_text = "ACHIEVEMENT UNLOCKED"
    header_bbox = engine.draw.textbbox((0, 0), header_text, font=header_font)
    header_w = header_bbox[2] - header_bbox[0]
    engine.draw.text(
        ((engine.width - header_w) // 2, 50),
        header_text, fill=(200, 200, 200), font=header_font
    )
    
    # Main badge display area (glowing circle)
    center_x = engine.width // 2
    center_y = 300
    radius = 140
    
    # Outer glow rings
    for i in range(5, 0, -1):
        glow_radius = radius + i * 15
        glow_alpha = 30 - i * 5
        glow_color = main_color[:3] + (glow_alpha,)
        engine.draw.ellipse(
            [center_x - glow_radius, center_y - glow_radius,
             center_x + glow_radius, center_y + glow_radius],
            outline=glow_color, width=3
        )
    
    # Main circle background
    engine.draw.ellipse(
        [center_x - radius, center_y - radius,
         center_x + radius, center_y + radius],
        fill=(30, 30, 40), outline=main_color, width=4
    )
    
    # Inner circle (lighter)
    inner_r = radius - 20
    engine.draw.ellipse(
        [center_x - inner_r, center_y - inner_r,
         center_x + inner_r, center_y + inner_r],
        fill=(40, 40, 55)
    )
    
    # Large icon
    icon_font = engine._get_font(100)
    icon_bbox = engine.draw.textbbox((0, 0), icon, font=icon_font)
    icon_w = icon_bbox[2] - icon_bbox[0]
    icon_h = icon_bbox[3] - icon_bbox[1]
    engine.draw.text(
        (center_x - icon_w//2, center_y - icon_h//2 - 20),
        icon, fill=hex_color, font=icon_font
    )
    
    # Badge name (large)
    name_font = engine._get_font(38, bold=True)
    name_bbox = engine.draw.textbbox((0, 0), name, font=name_font)
    name_w = name_bbox[2] - name_bbox[0]
    engine.draw.text(
        (center_x - name_w//2, 480),
        name, fill="white", font=name_font
    )
    
    # Rarity badge
    rarity_y = 540
    rarity_font = engine._get_font(22, bold=True)
    rarity_text = f"[{rarity.upper()}]"
    rarity_bbox = engine.draw.textbbox((0, 0), rarity_text, font=rarity_font)
    rarity_w = rarity_bbox[2] - rarity_bbox[0]
    engine.draw.text(
        (center_x - rarity_w//2, rarity_y),
        rarity_text, fill=hex_color, font=rarity_font
    )
    
    # Earned date
    if earned_at:
        date_font = engine._get_font(16)
        date_text = f"Earned on {earned_at}"
        date_bbox = engine.draw.textbbox((0, 0), date_text, font=date_font)
        date_w = date_bbox[2] - date_bbox[0]
        engine.draw.text(
            (center_x - date_w//2, 585),
            date_text, fill=(150, 150, 150), font=date_font
        )
    
    # Decorative bottom bar
    bar_y = 650
    engine.draw.rectangle(
        [50, bar_y, engine.width - 50, bar_y + 4],
        fill=main_color
    )
    
    # XP points decoration
    xp_font = engine._get_font(18)
    xp_texts = ["+100 XP", "+50 Coins", "Rare Drop"]
    xp_start_x = 100
    xp_spacing = 170
    for i, xp in enumerate(xp_texts):
        xp_bbox = engine.draw.textbbox((0, 0), xp, font=xp_font)
        xp_w = xp_bbox[2] - xp_bbox[0]
        engine.draw.text(
            (xp_start_x + i * xp_spacing - xp_w//2, bar_y + 25),
            xp, fill=(180, 180, 180), font=xp_font
        )
    
    # Save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = date.today().strftime("%Y%m%d_%H%M%S")
    filename = f"gaming_badge_{timestamp}.png"
    filepath = OUTPUT_DIR / filename
    
    engine.img.save(filepath, "PNG", quality=95)
    logger.info(f"Gaming-style badge poster saved to: {filepath}")
    
    buffer = io.BytesIO()
    engine.img.save(buffer, format="PNG")
    import base64
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
