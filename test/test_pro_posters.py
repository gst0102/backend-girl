#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to generate PRO-level professional poster examples
"""
import sys
sys.path.insert(0, '.')

from app.services.poster_pro import (
    generate_spotify_wrapped_monthly,
    generate_instagram_couple_poster,
    generate_gaming_badge_poster,
)


def test_spotify_monthly():
    """Test Spotify Wrapped style monthly poster"""
    print("=" * 70)
    print("TESTING: Spotify Wrapped Style - Monthly Report")
    print("=" * 70)
    
    stats = {
        "poop_count": 18,
        "sleep_score": 92,
        "continuous_days": 15,
        "beat_percent": 85,
        "trend": [3, 5, 2, 7, 4, 6, 8],
    }
    
    try:
        base64_str = generate_spotify_wrapped_monthly(stats)
        print(f"[SUCCESS] Spotify-style monthly poster generated!")
        print(f"          Base64 length: {len(base64_str):,} characters")
        print(f"          File saved to: output/posters/spotify_monthly_*.png")
        return True
    except Exception as e:
        print(f"[FAILED] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_instagram_couple():
    """Test Instagram style couple poster"""
    print("\n" + "=" * 70)
    print("TESTING: Instagram Style - Couple Sync Report")
    print("=" * 70)
    
    info = {
        "sync_rate": 95,
        "bind_days": 365,
        "common_days": 120,
        "period_overlap": 12,
    }
    
    try:
        base64_str = generate_instagram_couple_poster(info)
        print(f"[SUCCESS] Instagram-style couple poster generated!")
        print(f"          Base64 length: {len(base64_str):,} characters")
        print(f"          File saved to: output/posters/instagram_couple_*.png")
        return True
    except Exception as e:
        print(f"[FAILED] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gaming_badge():
    """Test Gaming Achievement style badge poster"""
    print("\n" + "=" * 70)
    print("TESTING: Gaming Achievement Style - Badge Showcase")
    print("=" * 70)
    
    badge = {
        "name": "Early Bird Champion",
        "rarity": "Legendary",
        "icon": "\U0001f343",
        "earned_at": "2026-05-19",
    }
    
    try:
        base64_str = generate_gaming_badge_poster(badge)
        print(f"[SUCCESS] Gaming-style badge poster generated!")
        print(f"          Base64 length: {len(base64_str):,} characters")
        print(f"          File saved to: output/posters/gaming_badge_*.png")
        return True
    except Exception as e:
        print(f"[FAILED] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  PRO POSTER GENERATOR - PROFESSIONAL TEMPLATE TEST SUITE")
    print("=" * 70)
    
    results = []
    results.append(("Spotify Wrapped Monthly", test_spotify_monthly()))
    results.append(("Instagram Couple Sync", test_instagram_couple()))
    results.append(("Gaming Achievement Badge", test_gaming_badge()))
    
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)
    
    for name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        symbol = "\u2713" if success else "\u2717"
        print(f"{status} {symbol} {name}")
    
    all_passed = all(success for _, success in results)
    
    if all_passed:
        print("\n" + "=" * 70)
        print("  [ALL PASSED] All PRO posters generated successfully!")
        print("=" * 70)
        print("\n  Please check the output folder:")
        print("  -> output/posters/")
        print("\n  Compare these with the previous 'beautiful' version to see the upgrade!")
        sys.exit(0)
    else:
        print("\n[FAIL] Some tests failed")
        sys.exit(1)
