"""
fb_poster.py — stat-poster
Posts stat image + caption to Facebook Page.
No article URL comment needed for stat posts (content is self-contained).
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

FB_PAGE_ID      = os.getenv("FB_PAGE_ID", "")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN", "")
GRAPH_API_URL   = "https://graph.facebook.com/v19.0"


def post_to_facebook(image_path: str, caption: str) -> bool:
    if not FB_PAGE_ID or not FB_ACCESS_TOKEN:
        print("  ❌ FB_PAGE_ID or FB_ACCESS_TOKEN not set.")
        return False
    try:
        print("  📤 Uploading image...")
        with open(image_path, "rb") as f:
            upload_resp = requests.post(
                f"{GRAPH_API_URL}/{FB_PAGE_ID}/photos",
                data={"access_token": FB_ACCESS_TOKEN, "published": "false"},
                files={"source": f},
                timeout=60,
            )
        upload_data = upload_resp.json()
        if "id" not in upload_data:
            print(f"  ❌ Upload failed: {upload_data}")
            return False
        photo_id = upload_data["id"]
        print(f"  ✅ Photo uploaded (id: {photo_id})")

        print("  📢 Publishing post...")
        post_resp = requests.post(
            f"{GRAPH_API_URL}/{FB_PAGE_ID}/feed",
            data={
                "access_token":      FB_ACCESS_TOKEN,
                "message":           caption,
                "attached_media[0]": f'{{"media_fbid":"{photo_id}"}}',
            },
            timeout=30,
        )
        post_data = post_resp.json()
        if "id" in post_data:
            print(f"  ✅ Posted! ID: {post_data['id']}")
            return True
        print(f"  ❌ Post failed: {post_data}")
        return False
    except Exception as e:
        print(f"  ❌ Exception: {e}")
        return False


if __name__ == "__main__":
    print("FB_PAGE_ID set     :", bool(FB_PAGE_ID))
    print("FB_ACCESS_TOKEN set:", bool(FB_ACCESS_TOKEN))
