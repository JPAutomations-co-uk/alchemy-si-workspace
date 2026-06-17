#!/usr/bin/env python3
"""
Generate Flux Pro photorealistic backgrounds for ad creatives.

Reads the ad brief and copy, identifies which ads use photo templates,
generates appropriate Flux Pro prompts from brand/industry context,
and produces AI background images.

Usage:
    python .claude/skills/create-ad-creatives/scripts/generate_ad_backgrounds.py \
        --brief .tmp/ad_brief.json --copy .tmp/ad_copy.json --output .tmp/ad_backgrounds/
"""

import os
import sys
import json
import random
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

# Add execution/ to path for shared utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'execution'))
from generate_flux_image import generate_image
from load_brand_template import hex_to_description

DEFAULT_WORKERS = 3

# Templates that need photorealistic background images
PHOTO_TEMPLATES = {
    'ig_photo_overlay', 'ig_split_h', 'ig_split_v', 'ig_photo_frame',
    'ig_angled_split', 'ig_circle_photo', 'ig_corner_photo', 'hero_offer',
}

# Composition hints per template — tells Flux how to frame the shot
COMPOSITION_HINTS = {
    'ig_photo_overlay': 'wide atmospheric shot, clear space in lower 40% for text overlay, moody gradient-friendly',
    'ig_split_h': 'detailed scene filling upper frame, subject centered, clean horizontal composition',
    'ig_split_v': 'vertical portrait composition, subject positioned in left half of frame',
    'ig_photo_frame': 'clean centered subject with breathing room on all sides for thick border crop',
    'ig_angled_split': 'dramatic diagonal composition, strong subject in left portion of frame',
    'ig_circle_photo': 'centered portrait or detail shot, circular crop friendly, clean background',
    'ig_corner_photo': 'asymmetric composition, strong subject in upper-right quadrant, open left side',
    'hero_offer': 'professional product or service hero shot, clean and aspirational',
}

NEGATIVE_PROMPT = (
    "blurry, watermark, low quality, cartoon, illustration, text, text overlay, "
    "3D render, words, letters, logo, stamp, amateur, overexposed, underexposed"
)


def dims_to_aspect(dims_str):
    """Map ad dimensions to Flux Pro aspect ratio."""
    try:
        w, h = dims_str.lower().split('x')
        ratio = int(w) / int(h)
    except (ValueError, ZeroDivisionError):
        return "1:1"
    if abs(ratio - 1.0) < 0.05:
        return "1:1"
    if abs(ratio - 0.8) < 0.05:
        return "4:5"
    if abs(ratio - 0.5625) < 0.1:
        return "9:16"
    return "1:1"


def build_background_prompt(ad_request, copy_data, brief, template_name):
    """Build a Flux Pro prompt tailored to the ad's template and content."""
    industry = brief.get('industry', brief.get('brand_name', ''))
    target_audience = brief.get('target_audience', '')
    topic = ad_request.get('topic', '')

    # Get headline from copy for scene relevance
    headline = ''
    if copy_data:
        variations = copy_data.get('variations', [])
        if variations:
            headline = variations[0].get('headline', '')

    composition = COMPOSITION_HINTS.get(template_name, 'balanced professional composition')

    # Brand color context
    colors = brief.get('brand_colors', {})
    color_parts = []
    if primary := colors.get('primary'):
        color_parts.append(hex_to_description(primary))
    if accent := colors.get('accent'):
        color_parts.append(hex_to_description(accent))
    color_desc = f"color palette harmonizing with {' and '.join(color_parts)} tones" if color_parts else ""

    # Scene description from topic/headline
    scene = topic or headline or f"{industry} professional setting"

    prompt_parts = [
        f"Professional photorealistic image for {industry}",
        f"scene: {scene}",
        composition,
        color_desc,
        f"target audience: {target_audience}" if target_audience else "",
        "photorealistic, ultra sharp detail, professional photography, high-end editorial",
    ]

    return ", ".join(p for p in prompt_parts if p)


def generate_backgrounds(brief, all_copy, output_dir, api_token, workers=DEFAULT_WORKERS, model=None):
    """Generate Flux Pro backgrounds for all photo-template ads."""
    ad_requests = brief.get('ad_requests', [])
    os.makedirs(output_dir, exist_ok=True)

    # Build copy lookup by ad_index
    copy_lookup = {}
    for ac in all_copy:
        copy_lookup[ac.get('ad_index', 0)] = ac

    # Filter to photo templates only
    photo_ads = []
    for i, req in enumerate(ad_requests):
        template = req.get('template', '')
        ad_type = req.get('type', 'single')
        ad_idx = i

        if template in PHOTO_TEMPLATES:
            photo_ads.append((ad_idx, req, template))
        elif ad_type == 'carousel':
            # Carousels don't use photo backgrounds in current templates
            print(f"  Ad {ad_idx} ({template}): carousel, skipping background generation")
        else:
            print(f"  Ad {ad_idx} ({template}): text-only template, skipping background generation")

    if not photo_ads:
        print("No photo-template ads found. Skipping background generation.")
        manifest = {"backgrounds": []}
        manifest_path = os.path.join(output_dir, 'backgrounds_manifest.json')
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        return manifest_path

    print(f"\nGenerating {len(photo_ads)} background images...\n")

    backgrounds = []

    def _generate_one(ad_idx, ad_request, template_name):
        copy_data = copy_lookup.get(ad_idx)
        prompt = build_background_prompt(ad_request, copy_data, brief, template_name)
        dims = ad_request.get('dimensions', '1080x1080')
        aspect = dims_to_aspect(dims)

        filename = f"ad_{ad_idx}_bg.png"
        filepath = os.path.join(output_dir, filename)

        if os.path.exists(filepath):
            print(f"  Ad {ad_idx}: skipping existing {filename}")
            return {
                "ad_index": ad_idx,
                "template": template_name,
                "image_path": filepath,
                "prompt": prompt,
            }

        # Seed for reproducibility (only used when actually generating)
        seed = random.randint(1, 2**31)

        print(f"  Ad {ad_idx} ({template_name}): {prompt[:80]}...")

        img_bytes = generate_image(
            prompt, aspect, api_token,
            negative_prompt=NEGATIVE_PROMPT,
            seed=seed,
            model=model,
        )

        if img_bytes:
            with open(filepath, "wb") as f:
                f.write(img_bytes)
            print(f"  Ad {ad_idx}: saved {filename}")
            return {
                "ad_index": ad_idx,
                "template": template_name,
                "image_path": filepath,
                "prompt": prompt,
                "seed": seed,
            }
        else:
            print(f"  Ad {ad_idx}: FAILED to generate background")
            return None

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_generate_one, ad_idx, req, tpl): ad_idx
            for ad_idx, req, tpl in photo_ads
        }
        for future in as_completed(futures):
            result = future.result()
            if result:
                backgrounds.append(result)

    # Sort by ad_index for consistent ordering
    backgrounds.sort(key=lambda x: x["ad_index"])

    manifest = {"backgrounds": backgrounds}
    manifest_path = os.path.join(output_dir, 'backgrounds_manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"\nGenerated {len(backgrounds)}/{len(photo_ads)} backgrounds")
    print(f"Manifest: {manifest_path}")
    return manifest_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate Flux Pro photorealistic backgrounds for ad creatives",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python generate_ad_backgrounds.py --brief .tmp/ad_brief.json --copy .tmp/ad_copy.json --output .tmp/ad_backgrounds/
  python generate_ad_backgrounds.py --brief .tmp/ad_brief.json --copy .tmp/ad_copy.json --model black-forest-labs/flux-2-pro --output .tmp/ad_backgrounds/"""
    )
    parser.add_argument("--brief", "-b", required=True, help="Ad brief JSON path")
    parser.add_argument("--copy", "-c", required=True, help="Ad copy JSON path")
    parser.add_argument("--output", "-o", default=".tmp/ad_backgrounds/", help="Output directory")
    parser.add_argument("--workers", "-w", type=int, default=DEFAULT_WORKERS, help="Parallel workers")
    parser.add_argument("--model", "-m", help="Replicate model (default: black-forest-labs/flux-pro)")

    args = parser.parse_args()

    api_token = os.getenv("REPLICATE_API_TOKEN")
    if not api_token:
        print("Error: REPLICATE_API_TOKEN not set in .env", file=sys.stderr)
        sys.exit(1)

    with open(args.brief, 'r') as f:
        brief = json.load(f)
    with open(args.copy, 'r') as f:
        all_copy = json.load(f)

    generate_backgrounds(brief, all_copy, args.output, api_token,
                         workers=args.workers, model=args.model)


if __name__ == "__main__":
    main()
