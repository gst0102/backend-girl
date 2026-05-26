#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test all poster templates and generate examples
"""
import sys
sys.path.insert(0, '.')

from app.services.poster_templates_extended import (
    create_xiaohongshu_monthly,
    create_cute_cartoon_monthly, 
    create_minimal_japanese_monthly,
    create_vintage_newspaper_monthly,
    get_available_templates,
)


def test_all_templates():
    """Test all extended templates"""
    print("=" * 60)
    print("TESTING ALL POSTER TEMPLATES")
    print("=" * 60)
    
    stats = {
        "poop_count": 20,
        "sleep_score": 88,
        "continuous_days": 18,
        "beat_percent": 82,
        "trend": [3, 5, 2, 7, 4, 6, 8],
    }
    
    templates = [
        ("小红书风格", create_xiaohongshu_monthly),
        ("卡通手绘风", create_cute_cartoon_monthly),
        ("简约日系", create_minimal_japanese_monthly),
        ("复古报纸", create_vintage_newspaper_monthly),
    ]
    
    results = []
    for name, func in templates:
        print(f"\nTesting {name}...")
        try:
            base64_str = func(stats)
            print(f"  [OK] Generated successfully! (Size: {len(base64_str):,} chars)")
            results.append((name, True))
        except Exception as e:
            print(f"  [FAIL] Error: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("AVAILABLE TEMPLATES")
    print("=" * 60)
    
    available = get_available_templates()
    for t in available:
        print(f"  - {t['key']}: {t['name']}")
        print(f"    {t['description']}")
    
    return all(success for _, success in results)


if __name__ == "__main__":
    success = test_all_templates()
    
    if success:
        print("\n✅ All templates generated successfully!")
        print("Check output/posters/ folder for all examples.")
        sys.exit(0)
    else:
        print("\n❌ Some templates failed")
        sys.exit(1)
