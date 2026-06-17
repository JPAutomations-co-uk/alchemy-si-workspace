#!/usr/bin/env python3
"""
Verify the full Instagram content workflow end-to-end.

This script:
1. Creates dummy input data (calendar, prompts).
2. Runs asset generation scripts (carousel, video).
3. Runs posting script (dry-run).
4. Verifies output artifacts exist.
"""

import os
import sys
import json
import subprocess
import shutil

def run_command(cmd):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {cmd}")
        print(result.stderr)
        return False
    print(result.stdout)
    return True

def main():
    print("Starting workflow verification...")
    
    # Setup paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tmp_dir = os.path.join(base_dir, ".tmp")
    assets_dir = os.path.join(tmp_dir, "dummy_assets")
    
    # Clean previous run
    if os.path.exists(assets_dir):
        shutil.rmtree(assets_dir)
    os.makedirs(assets_dir, exist_ok=True)
    
    # 1. Create dummy data
    print("\n1. Creating dummy data...")
    calendar_path = os.path.join(tmp_dir, "dummy_calendar.json")
    prompts_path = os.path.join(tmp_dir, "dummy_prompts.json")
    
    calendar_data = [
        {
            "date": "2026-02-13",
            "topic": "Test Carousel",
            "format": "carousel",
            "content_angle": "Testing generation",
            "caption": "This is a test carousel"
        },
        {
            "date": "2026-02-13",
            "day": 13,
            "topic": "Test Video",
            "format": "video",
            "caption": "This is a test video"
        }
    ]
    
    prompts_data = [
        {
            "day": "13",
            "topic": "Test Video",
            "higgsfield_prompt": "A futuristic building with neon lights"
        }
    ]
    
    with open(calendar_path, "w") as f:
        json.dump(calendar_data, f, indent=2)
        
    with open(prompts_path, "w") as f:
        json.dump(prompts_data, f, indent=2)
        
    print("Dummy data created.")

    # 2. Run Image Generation
    print("\n2. Running Image Generation...")
    cmd_image = f"python3 execution/generate_carousel_images.py --calendar '{calendar_path}' --output '{assets_dir}'"
    if not run_command(cmd_image):
        print("Image generation failed.")
        sys.exit(1)
        
    # Verify images
    carousel_dir = os.path.join(assets_dir, "2026-02-13_Test_Carousel")
    if not os.path.exists(carousel_dir) or not os.listdir(carousel_dir):
        print(f"Verification failed: No images generated in {carousel_dir}")
        sys.exit(1)
    print("Images verified.")

    # 3. Run Video Generation
    print("\n3. Running Video Generation...")
    cmd_video = f"python3 execution/generate_higgsfield_video.py --prompts '{prompts_path}' --output '{assets_dir}'"
    if not run_command(cmd_video):
        print("Video generation failed.")
        sys.exit(1)
        
    # Verify video
    video_path = os.path.join(assets_dir, "13_Test_Video.mp4")
    if not os.path.exists(video_path):
        print(f"Verification failed: Video not found at {video_path}")
        sys.exit(1)
    print("Video verified.")

    # 4. Run Posting (Dry Run)
    print("\n4. Running Posting (Dry Run)...")
    cmd_post = f"python3 execution/post_to_instagram.py --calendar '{calendar_path}' --assets '{assets_dir}' --date 2026-02-13 --dry-run"
    if not run_command(cmd_post):
        print("Posting script failed.")
        sys.exit(1)
        
    print("\nSUCCESS: Full workflow verified!")

if __name__ == "__main__":
    main()
