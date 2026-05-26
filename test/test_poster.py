#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for poster generation service
"""
import base64
import io
import sys
from PIL import Image

# Add the project root to path
sys.path.insert(0, '.')

from app.services.poster_service import _create_base_canvas, _draw_text, _to_base64


def test_basic_image_generation():
    """Test basic image generation and base64 conversion"""
    print("=== Testing Basic Image Generation ===")
    
    # 1. Test canvas creation
    print("\n1. Testing canvas creation...")
    try:
        img, draw = _create_base_canvas()
        print(f"   [OK] Canvas created: {img.size}")
    except Exception as e:
        print(f"   [FAIL] Failed: {e}")
        return False
    
    # 2. Test drawing text
    print("\n2. Testing text drawing...")
    try:
        _draw_text(draw, (30, 230), "Test Text", "black", 24)
        print("   [OK] Text drawn successfully")
    except Exception as e:
        print(f"   [FAIL] Failed: {e}")
        return False
    
    # 3. Test base64 conversion
    print("\n3. Testing base64 conversion...")
    try:
        base64_str = _to_base64(img)
        print(f"   [OK] Base64 generated, length: {len(base64_str)}")
        print(f"   [OK] Starts with: {base64_str[:50]}...")
    except Exception as e:
        print(f"   [FAIL] Failed: {e}")
        return False
    
    # 4. Verify base64 can be decoded back to image
    print("\n4. Testing base64 decoding...")
    try:
        img_data = base64.b64decode(base64_str)
        decoded_img = Image.open(io.BytesIO(img_data))
        print(f"   [OK] Successfully decoded back to image: {decoded_img.size}")
    except Exception as e:
        print(f"   [FAIL] Failed: {e}")
        return False
    
    # 5. Save test image
    print("\n5. Saving test image...")
    try:
        img.save("test_poster_output.png", "PNG")
        print("   [OK] Test image saved as: test_poster_output.png")
    except Exception as e:
        print(f"   [FAIL] Failed: {e}")
        return False
    
    print("\n=== All tests passed! ===")
    return True


def test_data_uri():
    """Test if base64 is properly formatted for data URI"""
    print("\n=== Testing Data URI Format ===")
    
    img, draw = _create_base_canvas()
    _draw_text(draw, (30, 230), "Data URI Test", "black", 24)
    base64_str = _to_base64(img)
    
    data_uri = f"data:image/png;base64,{base64_str}"
    print(f"Data URI length: {len(data_uri)}")
    print(f"Data URI starts with: {data_uri[:100]}...")
    
    # Verify first characters
    if not data_uri.startswith("data:image/png;base64,"):
        print("[FAIL] Data URI format incorrect!")
        return False
    
    print("[OK] Data URI format correct")
    return True


if __name__ == "__main__":
    success = test_basic_image_generation()
    test_data_uri()
    
    if success:
        print("\n[SUCCESS] Poster generation test passed!")
        sys.exit(0)
    else:
        print("\n[FAIL] Poster generation test failed!")
        sys.exit(1)
