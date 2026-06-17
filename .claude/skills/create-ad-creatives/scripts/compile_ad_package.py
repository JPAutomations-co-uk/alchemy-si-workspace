#!/usr/bin/env python3
"""
Compile ad creatives into an organized deliverable package.

Organizes PNG images into per-ad subfolders with clean naming, generates a
full manifest, and optionally exports Meta Business Suite compatible JSON.

Usage:
    python .claude/skills/create-ad-creatives/scripts/compile_ad_package.py --images .tmp/ad_images/ --copy .tmp/ad_copy.json --brief .tmp/ad_brief.json --output .tmp/ad_package/
    python .claude/skills/create-ad-creatives/scripts/compile_ad_package.py --images .tmp/ad_images/ --copy .tmp/ad_copy.json --brief .tmp/ad_brief.json --meta-export --output .tmp/ad_package/
"""

import os
import sys
import json
import shutil
import argparse
import re
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'execution'))


def slugify(text):
    """Convert text to filesystem-safe slug."""
    return re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')[:50]


def compile_package(images_dir, copy_path, brief_path, output_dir, meta_export=False):
    """Organize all creatives into a clean deliverable package."""

    with open(brief_path, 'r') as f:
        brief = json.load(f)
    with open(copy_path, 'r') as f:
        all_copy = json.load(f)

    # Load image manifest
    manifest_path = os.path.join(images_dir, 'manifest.json')
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            image_manifest = json.load(f)
    else:
        # Fallback: scan directory for PNGs
        image_manifest = []
        for f in sorted(os.listdir(images_dir)):
            if f.endswith('.png'):
                image_manifest.append({'filename': f})

    # Create package directory
    brand_slug = slugify(brief.get('brand_name', 'brand'))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_dir = os.path.join(output_dir, f"ad_package_{brand_slug}_{timestamp}")
    os.makedirs(package_dir, exist_ok=True)

    # Group images by ad
    ads = {}
    for item in image_manifest:
        filename = item.get('filename', '')
        ad_idx = item.get('ad_index', 0)
        variation = item.get('variation', 1)
        template = item.get('template', 'unknown')
        ad_type = item.get('type', 'single')
        key = f"{ad_idx}_{template}_v{variation}"

        if key not in ads:
            ads[key] = {
                'ad_index': ad_idx,
                'type': ad_type,
                'template': template,
                'variation': variation,
                'files': []
            }
        ads[key]['files'].append(item)

    # Copy and organize files
    package_manifest = {
        'brand': brief.get('brand_name', ''),
        'generated_at': datetime.now().isoformat(),
        'total_creatives': len(ads),
        'creatives': []
    }

    for key, ad_info in sorted(ads.items()):
        ad_dir = os.path.join(package_dir, key)
        os.makedirs(ad_dir, exist_ok=True)

        # Copy images with clean names
        file_list = []
        for item in sorted(ad_info['files'], key=lambda x: x.get('slide_num') or 0):
            src = os.path.join(images_dir, item['filename'])
            if not os.path.exists(src):
                continue

            slide_num = item.get('slide_num')
            if slide_num:
                dst_name = f"slide_{slide_num}.png"
            else:
                dst_name = "image.png"

            dst = os.path.join(ad_dir, dst_name)
            shutil.copy2(src, dst)
            file_list.append(dst_name)

        # Write copy.json for this ad
        ad_idx = ad_info['ad_index']
        variation = ad_info['variation']
        copy_data = {}
        for ac in all_copy:
            if ac.get('ad_index') == ad_idx:
                vars_list = ac.get('variations', [])
                var_idx = min(variation - 1, len(vars_list) - 1)
                if vars_list:
                    copy_data = vars_list[var_idx]
                break

        copy_file = os.path.join(ad_dir, 'copy.json')
        with open(copy_file, 'w') as f:
            json.dump(copy_data, f, indent=2)

        # Add to manifest
        creative_entry = {
            'id': key,
            'type': ad_info['type'],
            'template': ad_info['template'],
            'variation': ad_info['variation'],
            'dimensions': f"{ad_info['files'][0].get('width', 1080)}x{ad_info['files'][0].get('height', 1080)}",
            'slide_count': len(file_list) if ad_info['type'] == 'carousel' else None,
            'files': file_list,
            'copy': copy_data
        }
        package_manifest['creatives'].append(creative_entry)

        print(f"  {key}/: {len(file_list)} files")

    # Save main manifest
    manifest_out = os.path.join(package_dir, 'manifest.json')
    with open(manifest_out, 'w') as f:
        json.dump(package_manifest, f, indent=2)

    # Optional: Meta Business Suite export
    if meta_export:
        try:
            from export_meta_scheduler import FORMAT_TO_META_TYPE
        except ImportError:
            FORMAT_TO_META_TYPE = {
                'carousel': 'CAROUSEL_ALBUM',
                'single': 'IMAGE',
                'image': 'IMAGE',
            }

        meta_posts = []
        for creative in package_manifest['creatives']:
            ad_type = creative['type']
            meta_type = FORMAT_TO_META_TYPE.get(ad_type, 'IMAGE')

            caption = ""
            copy = creative.get('copy', {})
            if copy:
                caption = copy.get('primary_text', '')
                hashtags = copy.get('hashtags', '')
                if hashtags and hashtags not in caption:
                    caption = f"{caption}\n\n{hashtags}"

            meta_posts.append({
                'publish_time': '',
                'caption': caption,
                'media_type': meta_type,
                'media_urls': [],
                'creative_id': creative['id'],
                'files': creative['files'],
                'notes': f"Template: {creative['template']}, Variation: {creative['variation']}"
            })

        meta_data = {
            'version': '1.0',
            'platform': 'instagram',
            'generated_at': datetime.now().isoformat(),
            'total_posts': len(meta_posts),
            'note': 'Upload images and set publish_time before importing to Meta Business Suite',
            'posts': meta_posts
        }

        meta_path = os.path.join(package_dir, 'meta_schedule.json')
        with open(meta_path, 'w') as f:
            json.dump(meta_data, f, indent=2)
        print(f"\n  Meta schedule saved to meta_schedule.json")

    print(f"\nPackage compiled to {package_dir}")
    print(f"Total creatives: {len(package_manifest['creatives'])}")

    return package_dir


def main():
    parser = argparse.ArgumentParser(
        description="Compile ad creatives into a deliverable package",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python compile_ad_package.py --images .tmp/ad_images/ --copy .tmp/ad_copy.json --brief .tmp/ad_brief.json --output .tmp/
  python compile_ad_package.py --images .tmp/ad_images/ --copy .tmp/ad_copy.json --brief .tmp/ad_brief.json --meta-export --output .tmp/"""
    )
    parser.add_argument("--images", "-i", required=True, help="Directory with PNG images")
    parser.add_argument("--copy", "-c", required=True, help="Ad copy JSON path")
    parser.add_argument("--brief", "-b", required=True, help="Ad brief JSON path")
    parser.add_argument("--meta-export", action="store_true", help="Generate Meta Business Suite JSON")
    parser.add_argument("--output", "-o", default=".tmp/", help="Output parent directory")

    args = parser.parse_args()

    compile_package(args.images, args.copy, args.brief, args.output, args.meta_export)


if __name__ == "__main__":
    main()
