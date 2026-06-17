#!/usr/bin/env python3
"""
Screenshot HTML ad creatives to pixel-perfect PNG images using Playwright.

Reads the manifest.json from generate_ad_html.py to set correct viewport
dimensions per file, then screenshots each HTML file at exact ad dimensions.

Usage:
    python .claude/skills/create-ad-creatives/scripts/screenshot_ads.py --input .tmp/ad_html/ --output .tmp/ad_images/
    python .claude/skills/create-ad-creatives/scripts/screenshot_ads.py --input .tmp/ad_html/ --output .tmp/ad_images/ --scale 2
"""

import os
import sys
import json
import argparse
import time


def check_playwright():
    """Check if Playwright and Chromium are available."""
    try:
        from playwright.sync_api import sync_playwright
        return True
    except ImportError:
        print("Error: Playwright not installed. Run: pip install playwright", file=sys.stderr)
        return False


def screenshot_html_files(input_dir, output_dir, scale=2):
    """Screenshot all HTML files in input_dir to PNGs in output_dir."""
    from playwright.sync_api import sync_playwright

    # Load manifest for dimensions
    manifest_path = os.path.join(input_dir, 'manifest.json')
    manifest = {}
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            manifest_list = json.load(f)
            manifest = {item['filename']: item for item in manifest_list}

    # Find all HTML files
    html_files = sorted([f for f in os.listdir(input_dir) if f.endswith('.html')])
    if not html_files:
        print("No HTML files found in input directory", file=sys.stderr)
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    print(f"Screenshotting {len(html_files)} HTML files at {scale}x scale...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for i, html_file in enumerate(html_files):
            # Get dimensions from manifest or default
            info = manifest.get(html_file, {})
            width = info.get('width', 1080)
            height = info.get('height', 1080)

            # Create page with exact viewport
            page = browser.new_page(
                viewport={'width': width, 'height': height},
                device_scale_factor=scale
            )

            # Navigate to HTML file
            file_path = os.path.abspath(os.path.join(input_dir, html_file))
            page.goto(f"file://{file_path}")

            # Wait for fonts to load
            page.wait_for_load_state('networkidle')
            time.sleep(0.5)  # Extra buffer for Google Fonts CDN

            # Screenshot
            output_filename = html_file.replace('.html', '.png')
            output_path = os.path.join(output_dir, output_filename)

            page.screenshot(
                path=output_path,
                type='png',
                clip={'x': 0, 'y': 0, 'width': width, 'height': height}
            )

            page.close()

            print(f"  [{i+1}/{len(html_files)}] {output_filename} ({width}x{height} @{scale}x)")

        browser.close()

    # Build output manifest from all screenshotted files
    output_manifest = []
    for html_file in html_files:
        info = manifest.get(html_file, {})
        entry = {**info}
        entry['filename'] = html_file.replace('.html', '.png')
        if 'width' not in entry:
            entry['width'] = 1080
        if 'height' not in entry:
            entry['height'] = 1080
        output_manifest.append(entry)

    manifest_out = os.path.join(output_dir, 'manifest.json')
    with open(manifest_out, 'w') as f:
        json.dump(output_manifest, f, indent=2)

    print(f"\nScreenshots saved to {output_dir} ({len(html_files)} files at {scale}x scale)")


def main():
    parser = argparse.ArgumentParser(
        description="Screenshot HTML ad creatives to PNG images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python screenshot_ads.py --input .tmp/ad_html/ --output .tmp/ad_images/
  python screenshot_ads.py --input .tmp/ad_html/ --output .tmp/ad_images/ --scale 2"""
    )
    parser.add_argument("--input", "-i", required=True, help="Input directory with HTML files")
    parser.add_argument("--output", "-o", default=".tmp/ad_images/", help="Output directory for PNGs")
    parser.add_argument("--scale", "-s", type=int, default=2, help="Device scale factor (default: 2 for retina)")

    args = parser.parse_args()

    if not os.path.isdir(args.input):
        print(f"Error: Input directory not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    if not check_playwright():
        print("\nTo install Playwright:", file=sys.stderr)
        print("  pip install playwright", file=sys.stderr)
        print("  playwright install chromium", file=sys.stderr)
        sys.exit(1)

    screenshot_html_files(args.input, args.output, args.scale)


if __name__ == "__main__":
    main()
