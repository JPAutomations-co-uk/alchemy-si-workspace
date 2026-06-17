#!/usr/bin/env python3
"""
Generate animated video ad creatives from HTML/CSS motion templates.

Uses Playwright to record CSS animations as video, then FFmpeg to convert
WebM → MP4 at Instagram-ready specs.

Usage:
    # Single video from template + brief:
    python3 generate_ad_video.py --template igv_gradient_flow --brief .tmp/ad_brief.json --copy .tmp/ad_copy.json --output .tmp/ad_videos/

    # Batch (all igv_ templates in brief's ad_requests):
    python3 generate_ad_video.py --brief .tmp/ad_brief.json --copy .tmp/ad_copy.json --output .tmp/ad_videos/

    # Quick single — no copy file needed, supply copy inline:
    python3 generate_ad_video.py --template igv_neon_pulse \
        --headline "We Scale Businesses" --subheadline "Without the Agency Markup" \
        --cta "Book a Call" --logo path/to/logo.png --output .tmp/

    # Preview a template with placeholder text:
    python3 generate_ad_video.py --template igv_gradient_flow --preview --output .tmp/
"""

import os
import sys
import json
import base64
import argparse
import subprocess
import tempfile
import shutil
import time
from html import escape
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), '..', 'templates')

# Default durations per template (seconds)
TEMPLATE_DURATIONS = {
    'igv_gradient_flow':  15,
    'igv_logo_reveal':    10,
    'igv_slide_sequence': 15,
    'igv_neon_pulse':     12,
    'igv_geometric':      15,
    'igv_typewriter':     12,
    'igv_counter':        10,
    'igv_split_reveal':   12,
    'igv_particle':       15,
    'igv_cinematic':      15,
    'igv_content_engine': 47,
    'igv_content_engine_v2': 47,
    'igv_mailpulse': 60,
}

# Video specs (Instagram + YouTube)
IG_SPECS = {
    '1080x1080': {'width': 1080, 'height': 1080, 'fps': 30},
    '1080x1350': {'width': 1080, 'height': 1350, 'fps': 30},
    '1080x1920': {'width': 1080, 'height': 1920, 'fps': 30},
    '1920x1080': {'width': 1920, 'height': 1080, 'fps': 30},
    '3840x2160': {'width': 3840, 'height': 2160, 'fps': 30},
}


def load_template(template_name):
    path = os.path.join(TEMPLATES_DIR, f"{template_name}.html")
    if not os.path.exists(path):
        print(f"Error: Template not found: {path}", file=sys.stderr)
        return None
    with open(path, 'r') as f:
        return f.read()


def encode_image(image_path):
    if not image_path or not os.path.exists(image_path):
        return ""
    try:
        ext = os.path.splitext(image_path)[1].lower()
        mime = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                '.webp': 'image/webp', '.svg': 'image/svg+xml'}.get(ext, 'image/png')
        with open(image_path, 'rb') as f:
            data = base64.b64encode(f.read()).decode('utf-8')
        return f'data:{mime};base64,{data}'
    except Exception:
        return ""


def get_brand_vars(brief):
    import urllib.parse
    import re

    def valid_hex(color, default):
        if color and re.match(r'^#[0-9a-fA-F]{3,6}$', color):
            return color
        return default

    colors = brief.get('brand_colors', {})
    fonts = brief.get('fonts', {})
    heading_font = fonts.get('heading', 'Inter')
    body_font = fonts.get('body', 'Inter')

    return {
        'primary_color':       valid_hex(colors.get('primary'), '#1A1A2E'),
        'secondary_color':     valid_hex(colors.get('secondary'), '#16213E'),
        'accent_color':        valid_hex(colors.get('accent'), '#E94560'),
        'text_light':          valid_hex(colors.get('text_light'), '#FFFFFF'),
        'text_dark':           valid_hex(colors.get('text_dark'), '#1A1A2E'),
        'bg_color':            valid_hex(colors.get('background'), '#F5F5F5'),
        'heading_font':        heading_font,
        'body_font':           body_font,
        'heading_font_encoded': urllib.parse.quote(heading_font),
        'body_font_encoded':   urllib.parse.quote(body_font),
        'brand_name':          escape(brief.get('brand_name', '')),
    }


def build_logo_html(brief):
    logo_path = brief.get('logo_path', '')
    b64 = encode_image(logo_path)
    if b64:
        return f'<img class="logo" src="{b64}" alt="Logo">'
    return ""


def build_hero_image_html(brief, css_class="hero-image"):
    hero_images = brief.get('hero_images', [])
    hero_path = hero_images[0] if hero_images else brief.get('hero_image', '')
    b64 = encode_image(hero_path)
    if b64:
        return f'<img class="{css_class}" src="{b64}" alt="">'
    return ""


def render_template(template_html, copy_data, brief, width, height, extra_vars=None):
    """Inject all variables into an HTML template string."""
    brand_vars = get_brand_vars(brief)
    logo_html = build_logo_html(brief)
    hero_image_html = build_hero_image_html(brief)

    vars_dict = dict(
        width=width,
        height=height,
        headline=escape(copy_data.get('headline', '')),
        subheadline=escape(copy_data.get('subheadline', '')),
        body=escape(copy_data.get('body', '')),
        cta=escape(copy_data.get('cta', brief.get('cta_text', 'Learn More'))),
        logo_html=logo_html,
        hero_image_html=hero_image_html,
        **brand_vars
    )
    if extra_vars:
        vars_dict.update(extra_vars)

    try:
        return template_html.format(**vars_dict)
    except KeyError as e:
        print(f"  Warning: Missing template variable {e}", file=sys.stderr)
        return None


def record_html_to_webm(html_path, output_webm, width, height, duration_secs, fps=30):
    """Use Playwright to record the HTML animation as a WebM video."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Error: playwright not installed. Run: pip install playwright && playwright install chromium", file=sys.stderr)
        return False

    # Create temp dir for Playwright video output
    video_dir = tempfile.mkdtemp()

    # For 4K: render at half viewport with 2x scale for crisp text
    if width >= 3840:
        viewport_w, viewport_h = width // 2, height // 2
        scale_factor = 2
    else:
        viewport_w, viewport_h = width, height
        scale_factor = 1

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=['--no-sandbox', '--disable-setuid-sandbox'])
            context = browser.new_context(
                viewport={"width": viewport_w, "height": viewport_h},
                device_scale_factor=scale_factor,
                record_video_dir=video_dir,
                record_video_size={"width": width, "height": height}
            )
            page = context.new_page()

            # Load the HTML file
            page.goto(f"file://{os.path.abspath(html_path)}")

            # Wait for fonts to load
            page.wait_for_load_state('networkidle', timeout=10000)
            page.wait_for_timeout(500)  # Extra settle time

            # Record for animation duration
            page.wait_for_timeout(int(duration_secs * 1000))

            context.close()
            browser.close()

            # Find the recorded video file
            video_files = list(Path(video_dir).glob("*.webm"))
            if not video_files:
                print("  Error: No video recorded by Playwright", file=sys.stderr)
                return False

            recorded = str(video_files[0])
            shutil.move(recorded, output_webm)
            return True

    except Exception as e:
        print(f"  Error during Playwright recording: {e}", file=sys.stderr)
        return False
    finally:
        shutil.rmtree(video_dir, ignore_errors=True)


def convert_webm_to_mp4(webm_path, mp4_path, fps=30):
    """Convert WebM to MP4 with Instagram-compatible codec settings."""
    if not shutil.which('ffmpeg'):
        print("Error: ffmpeg not found. Install: brew install ffmpeg", file=sys.stderr)
        return False

    cmd = [
        'ffmpeg', '-y',
        '-i', webm_path,
        '-c:v', 'libx264',
        '-preset', 'slow',
        '-crf', '8',
        '-pix_fmt', 'yuv420p',
        '-r', str(fps),
        '-movflags', '+faststart',
        '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',  # ensure even dimensions
        '-an',  # no audio (add audio separately if needed)
        mp4_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  FFmpeg error: {result.stderr[-500:]}", file=sys.stderr)
        return False
    return True


def generate_video(template_name, copy_data, brief, output_dir,
                   dimensions='1080x1080', duration=None, ad_index=0, variation=1):
    """Full pipeline: template → HTML → WebM → MP4."""
    template_html = load_template(template_name)
    if not template_html:
        return None

    specs = IG_SPECS.get(dimensions, IG_SPECS['1080x1080'])
    width, height = specs['width'], specs['height']
    fps = specs['fps']
    duration_secs = duration or TEMPLATE_DURATIONS.get(template_name, 15)

    os.makedirs(output_dir, exist_ok=True)

    # For 4K: template CSS uses viewport coords (half of output)
    tmpl_w = width // 2 if width >= 3840 else width
    tmpl_h = height // 2 if width >= 3840 else height

    # Render HTML with injected variables
    html_content = render_template(template_html, copy_data, brief, tmpl_w, tmpl_h)
    if not html_content:
        return None

    # Write temp HTML file
    tmp_html = os.path.join(output_dir, f"_tmp_{template_name}_{ad_index}.html")
    with open(tmp_html, 'w') as f:
        f.write(html_content)

    base_name = f"vid_{ad_index}_v{variation}_{template_name}"
    webm_path = os.path.join(output_dir, f"{base_name}.webm")
    mp4_path  = os.path.join(output_dir, f"{base_name}.mp4")

    print(f"  Recording {template_name} ({width}×{height}, {duration_secs}s)...")
    start = time.time()

    ok = record_html_to_webm(tmp_html, webm_path, width, height, duration_secs, fps)
    if not ok:
        os.unlink(tmp_html)
        return None

    print(f"  Converting to MP4...")
    ok = convert_webm_to_mp4(webm_path, mp4_path, fps)

    # Cleanup intermediates
    os.unlink(tmp_html)
    if os.path.exists(webm_path):
        os.unlink(webm_path)

    if not ok:
        return None

    elapsed = time.time() - start
    file_size_mb = os.path.getsize(mp4_path) / 1024 / 1024
    print(f"  Done: {mp4_path} ({file_size_mb:.1f}MB, {elapsed:.1f}s)")

    return {
        'filename': os.path.basename(mp4_path),
        'path': mp4_path,
        'template': template_name,
        'width': width,
        'height': height,
        'duration': duration_secs,
        'fps': fps,
        'ad_index': ad_index,
        'variation': variation,
        'type': 'video',
    }


def build_preview_brief(args):
    """Build a minimal brief from CLI args for quick preview."""
    return {
        'brand_name': args.brand_name or 'Your Brand',
        'brand_colors': {
            'primary':    args.primary or '#1A1A2E',
            'secondary':  args.secondary or '#16213E',
            'accent':     args.accent or '#E94560',
            'text_light': '#FFFFFF',
            'text_dark':  '#1A1A2E',
            'background': '#F5F5F5',
        },
        'fonts': {'heading': args.heading_font or 'Inter', 'body': args.body_font or 'Inter'},
        'logo_path':    args.logo or '',
        'hero_images':  [args.hero_image] if args.hero_image else [],
        'cta_text':     args.cta or 'Learn More',
    }


def build_preview_copy(args):
    """Build copy_data from CLI args."""
    return {
        'headline':    args.headline or 'Your Headline Here',
        'subheadline': args.subheadline or 'Your supporting message goes here.',
        'body':        args.body or '',
        'cta':         args.cta or 'Learn More',
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate animated Instagram video ads from HTML/CSS motion templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  # From brief + copy files:
  python3 generate_ad_video.py --brief .tmp/ad_brief.json --copy .tmp/ad_copy.json --output .tmp/ad_videos/

  # Single template preview:
  python3 generate_ad_video.py --template igv_gradient_flow --preview --output .tmp/

  # Inline copy:
  python3 generate_ad_video.py --template igv_neon_pulse \\
      --headline "We Scale Businesses" --subheadline "Book a free call today" \\
      --brand-name "Acme Agency" --accent "#FF6B35" --output .tmp/

Available video templates:
  igv_gradient_flow   igv_logo_reveal    igv_slide_sequence  igv_neon_pulse
  igv_geometric       igv_typewriter     igv_counter         igv_split_reveal
  igv_particle        igv_cinematic
"""
    )

    # Source options (mutually exclusive)
    src = parser.add_argument_group('Input source')
    src.add_argument('--brief', '-b', help='Ad brief JSON path')
    src.add_argument('--copy',  '-c', help='Ad copy JSON path')
    src.add_argument('--preview', action='store_true', help='Preview mode — use placeholder copy')

    # Template selection
    parser.add_argument('--template', '-t', help='Specific video template name (e.g. igv_gradient_flow)')
    parser.add_argument('--all-templates', action='store_true', help='Render all igv_ templates')

    # Inline copy/brand (for quick use without JSON files)
    parser.add_argument('--headline',    help='Headline text')
    parser.add_argument('--subheadline', help='Subheadline / supporting text')
    parser.add_argument('--body',        help='Body text')
    parser.add_argument('--cta',         help='CTA button text')
    parser.add_argument('--brand-name',  dest='brand_name', help='Brand name')
    parser.add_argument('--logo',        help='Path to logo image')
    parser.add_argument('--hero-image',  dest='hero_image', help='Path to hero/background image')
    parser.add_argument('--primary',     help='Primary brand color (hex)')
    parser.add_argument('--secondary',   help='Secondary brand color (hex)')
    parser.add_argument('--accent',      help='Accent color (hex)')
    parser.add_argument('--heading-font', dest='heading_font', help='Heading Google Font name')
    parser.add_argument('--body-font',    dest='body_font',    help='Body Google Font name')

    # Output options
    parser.add_argument('--output',     '-o', default='.tmp/ad_videos/', help='Output directory')
    parser.add_argument('--dimensions', '-d', default='1080x1080',
                        choices=list(IG_SPECS.keys()), help='Video dimensions')
    parser.add_argument('--duration',   type=float, help='Override animation duration (seconds)')
    parser.add_argument('--variation',  '-v', type=int, default=1, help='Copy variation to use')

    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    # ── Build brief and copy ────────────────────────────────────────────────
    if args.brief and os.path.exists(args.brief):
        with open(args.brief) as f:
            brief = json.load(f)
    else:
        brief = build_preview_brief(args)

    if args.copy and os.path.exists(args.copy):
        with open(args.copy) as f:
            all_copy = json.load(f)
        # Filter to video-type ad requests only
        video_ads = [a for a in all_copy if a.get('type') == 'video']
        if not video_ads and not args.template:
            print("No video ad requests in copy file. Use --template to specify one, or add type:video entries.")
            sys.exit(1)
    else:
        video_ads = []

    # ── Determine templates to render ──────────────────────────────────────
    if args.all_templates:
        templates_to_render = list(TEMPLATE_DURATIONS.keys())
    elif args.template:
        templates_to_render = [args.template]
    elif video_ads:
        templates_to_render = [a.get('template', 'igv_gradient_flow') for a in video_ads]
    else:
        print("Specify --template, --all-templates, or include video ad_requests in your copy file.")
        sys.exit(1)

    # ── Render each template ────────────────────────────────────────────────
    manifest = []
    for i, tpl_name in enumerate(templates_to_render):
        print(f"\n[{i+1}/{len(templates_to_render)}] {tpl_name}")

        # Get copy for this ad
        if video_ads and i < len(video_ads):
            ad_copy_entry = video_ads[i]
            variations = ad_copy_entry.get('variations', [{}])
            var_idx = min(args.variation - 1, len(variations) - 1)
            copy_data = variations[var_idx] if variations else {}
        else:
            copy_data = build_preview_copy(args)

        result = generate_video(
            template_name=tpl_name,
            copy_data=copy_data,
            brief=brief,
            output_dir=args.output,
            dimensions=args.dimensions,
            duration=args.duration,
            ad_index=i,
            variation=args.variation,
        )

        if result:
            manifest.append(result)
        else:
            print(f"  FAILED: {tpl_name}")

    # ── Save manifest ───────────────────────────────────────────────────────
    if manifest:
        manifest_path = os.path.join(args.output, 'video_manifest.json')
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        print(f"\n✓ {len(manifest)} video(s) generated in {args.output}")
        print(f"  Manifest: {manifest_path}")
    else:
        print("\nNo videos generated.")
        sys.exit(1)


if __name__ == '__main__':
    main()
