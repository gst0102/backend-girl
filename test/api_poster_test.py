#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Helper script to test the poster API endpoint.
This shows how to properly decode the base64 response.
"""
import base64
import json
import sys


def decode_base64_to_image():
    """
    Example: How to decode the API response to an image file.
    
    The API returns JSON like:
    {
        "code": 0,
        "message": "success",
        "data": {
            "image_base64": "iVBORw0KGgo..."
        }
    }
    """
    print("=== API Response Decoding Example ===")
    
    # Example response (replace with actual API response)
    example_response = '''
    {
        "code": 0,
        "message": "success",
        "data": {
            "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAlgAAAMgCAIAAABwAouTAAARkk..."
        }
    }
    '''
    
    print("\nStep 1: Parse JSON response")
    try:
        resp_json = json.loads(example_response)
        print("[OK] JSON parsed successfully")
    except json.JSONDecodeError as e:
        print(f"[FAIL] Failed to parse JSON: {e}")
        return False
    
    print("\nStep 2: Extract base64 from data")
    try:
        base64_str = resp_json["data"]["image_base64"]
        print(f"[OK] Extracted base64, length: {len(base64_str)}")
    except KeyError as e:
        print(f"[FAIL] Missing key in response: {e}")
        print(f"Response keys: {resp_json.keys()}")
        if "data" in resp_json:
            print(f"Data keys: {resp_json['data'].keys()}")
        return False
    
    print("\nStep 3: Decode base64")
    try:
        img_data = base64.b64decode(base64_str)
        print(f"[OK] Decoded successfully, size: {len(img_data)} bytes")
    except Exception as e:
        print(f"[FAIL] Failed to decode base64: {e}")
        return False
    
    print("\nStep 4: Save as PNG")
    try:
        with open("api_poster_output.png", "wb") as f:
            f.write(img_data)
        print("[OK] Image saved as: api_poster_output.png")
    except Exception as e:
        print(f"[FAIL] Failed to save image: {e}")
        return False
    
    print("\n=== Decoding Complete! ===")
    return True


def show_curl_commands():
    """Show example curl commands"""
    print("\n=== Example CURL Commands ===")
    print("\n1. Generate couple poster (saves raw response):")
    print('''
curl -X POST http://localhost:8000/api/poster/generate \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"template":"couple"}' \\
  -o poster_response.json
''')
    
    print("\n2. Then decode and save the image using Python:")
    print('''
import json, base64
with open('poster_response.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
img_data = base64.b64decode(data['data']['image_base64'])
with open('poster.png', 'wb') as f:
    f.write(img_data)
''')
    
    print("\n3. Or use PowerShell to decode:")
    print('''
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/poster/generate" -Method Post -Headers @{"Authorization"="Bearer YOUR_TOKEN"} -Body '{"template":"couple"}' -ContentType "application/json"
[IO.File]::WriteAllBytes("poster.png", [Convert]::FromBase64String($response.data.image_base64))
''')


if __name__ == "__main__":
    decode_base64_to_image()
    show_curl_commands()
