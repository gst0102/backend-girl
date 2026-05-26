#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate a complete example poster with all elements
"""
import sys
sys.path.insert(0, '.')

from datetime import date
from app.services.poster_service import _create_base_canvas, _draw_text, _to_base64


def generate_complete_example():
    """Generate a complete poster with all UI elements"""
    print("Generating complete example poster...")
    
    img, draw = _create_base_canvas()
    
    # Title section (green background already drawn)
    _draw_text(draw, (30, 60), "Monthly Report", "white", 36)
    _draw_text(draw, (30, 120), f"{date.today().isoformat()}", "white", 18)
    
    # Stats boxes
    stats = [
        ("Poop Count:", "15 times"),
        ("Sleep Score:", "85 points"),
        ("Streak Days:", "12 days"),
        ("Beat Users:", "78%"),
    ]
    
    y_pos = 230
    for label, value in stats:
        # Draw box background
        draw.rectangle([30, y_pos, 570, y_pos + 50], fill=(245, 245, 245), outline=(220, 220, 220))
        # Draw text
        _draw_text(draw, (50, y_pos + 8), f"{label} {value}", "black", 22)
        y_pos += 70
    
    # Trend line
    trend = [1, 2, 1, 3, 2, 4, 3]
    trend_text = " ".join(str(x) for x in trend)
    _draw_text(draw, (30, 520), f"Recent 7 days trend: {trend_text}", "black", 18)
    
    # Save as PNG
    output_path = "complete_poster_example.png"
    img.save(output_path, "PNG")
    print(f"[OK] Complete poster saved to: {output_path}")
    
    # Also test base64
    base64_str = _to_base64(img)
    print(f"[OK] Base64 length: {len(base64_str)} characters")
    
    return output_path


if __name__ == "__main__":
    output_file = generate_complete_example()
    print(f"\n✓ Please open {output_file} to see the complete poster!")
