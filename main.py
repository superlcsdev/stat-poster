"""
main.py — stat-poster
Runs Tue/Thu/Sat at 6:00 PM SGT.

Run modes:
  python main.py                   → full pipeline
  python main.py --dry-run         → generate without posting
  python main.py --topic sgd_php   → force a specific topic
"""

import argparse
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from stat_generator  import generate_stat, get_topic_for_today, TOPICS
from image_generator import create_stat_image
from fb_poster       import post_to_facebook

OUTPUT_DIR = "output_images"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def run_pipeline(dry_run: bool = False, topic: str = None):
    print("\n" + "=" * 60)
    print("  📊  Stat Post Auto-Poster")
    print("  📅  " + datetime.now().strftime("%Y-%m-%d %H:%M") + " UTC")
    print("=" * 60)

    # ── Step 1: Generate stat ─────────────────────────────────────
    if topic and topic not in TOPICS:
        print(f"❌ Invalid topic '{topic}'. Choose from: {', '.join(TOPICS)}")
        sys.exit(1)

    print(f"\n[1/3] Generating stat post...")
    result  = generate_stat(topic)
    caption = result["caption"]
    topic   = result["topic"]

    print(f"  🏷️  Topic  : {topic}")
    print(f"  📝 Preview: {caption[:100]}...")

    # ── Step 2: Create image ──────────────────────────────────────
    print(f"\n[2/3] Creating image...")
    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_path  = os.path.join(OUTPUT_DIR, f"stat_{timestamp}.jpg")
    result_path = create_stat_image(caption, image_path, topic=topic)

    if not result_path:
        print("❌ Image creation failed.")
        sys.exit(1)

    # ── Step 3: Post to Facebook ──────────────────────────────────
    if dry_run:
        print(f"\n[3/3] DRY RUN — skipping Facebook post.")
        print(f"  🖼️  Image  : {result_path}")
        print(f"\n{'─'*60}")
        print(caption)
        print(f"{'─'*60}")
        print("\n✅ Dry run complete!")
        return

    print(f"\n[3/3] Posting to Facebook...")
    success = post_to_facebook(image_path=result_path, caption=caption)
    if success:
        print("\n🎉 Stat post published!")
    else:
        print("\n❌ Facebook post failed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stat Post Auto-Poster")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--topic",   type=str, default=None,
                        help=f"Force topic: {', '.join(TOPICS)}")
    args = parser.parse_args()
    run_pipeline(dry_run=args.dry_run, topic=args.topic)
