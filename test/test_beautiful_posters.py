#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to generate beautiful poster examples
"""
import sys
sys.path.insert(0, '.')

from app.services.poster_templates import (
    create_beautiful_monthly_poster,
    create_beautiful_couple_poster,
    create_beautiful_badge_poster,
)


def test_monthly_poster():
    """Test monthly poster generation"""
    print("=" * 60)
    print("Testing Beautiful Monthly Poster")
    print("=" * 60)
    
    stats = {
        "poop_count": 15,
        "sleep_score": 85,
        "continuous_days": 12,
        "beat_percent": 78,
        "trend": [1, 2, 3, 4, 5, 6, 7],
    }
    
    try:
        base64_str = create_beautiful_monthly_poster(stats)
        print(f"[OK] Monthly poster generated successfully!")
        print(f"     Base64 length: {len(base64_str)} characters")
        print(f"     Saved to: output/posters/monthly_*.png")
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_couple_poster():
    """Test couple poster generation"""
    print("\n" + "=" * 60)
    print("Testing Beautiful Couple Poster")
    print("=" * 60)
    
    info = {
        "sync_rate": 92,
        "bind_days": 180,
        "common_days": 45,
        "period_overlap": 8,
    }
    
    try:
        base64_str = create_beautiful_couple_poster(info)
        print(f"[OK] Couple poster generated successfully!")
        print(f"     Base64 length: {len(base64_str)} characters")
        print(f"     Saved to: output/posters/couple_*.png")
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_badge_poster():
    """Test badge poster generation"""
    print("\n" + "=" * 60)
    print("Testing Beautiful Badge Poster")
    print("=" * 60)
    
    badge = {
        "name": "Early Bird",
        "rarity": "Legendary",
        "icon": "\U0001f343",
        "earned_at": "2026-05-19",
    }
    
    try:
        base64_str = create_beautiful_badge_poster(badge)
        print(f"[OK] Badge poster generated successfully!")
        print(f"     Base64 length: {len(base64_str)} characters")
        print(f"     Saved to: output/posters/badge_*.png")
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("BEAUTIFUL POSTER GENERATOR - TEST SUITE")
    print("=" * 60)
    
    results = []
    results.append(("Monthly Poster", test_monthly_poster()))
    results.append(("Couple Poster", test_couple_poster()))
    results.append(("Badge Poster", test_badge_poster()))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {name}")
    
    all_passed = all(success for _, success in results)
    
    if all_passed:
        print("\n[SUCCESS] All beautiful posters generated!")
        print("\nPlease check the output folder:")
        print("  -> output/posters/")
        sys.exit(0)
    else:
        print("\n[FAIL] Some tests failed")
        sys.exit(1)
