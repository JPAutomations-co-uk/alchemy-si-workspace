#!/usr/bin/env python3
"""
Parse ad brief from JSON file, website URL, or text prompt.

Normalizes any input format into a standardized ad_brief.json with brand colors,
fonts, assets, and ad requests ready for the creative pipeline.

Usage:
    python .claude/skills/create-ad-creatives/scripts/parse_ad_brief.py --json brief.json --output .tmp/ad_brief.json
    python .claude/skills/create-ad-creatives/scripts/parse_ad_brief.py --url "https://example.com" --output .tmp/ad_brief.json
    python .claude/skills/create-ad-creatives/scripts/parse_ad_brief.py --prompt "SaaS company called Acme..." --output .tmp/ad_brief.json
"""

import os
import sys
import json
import re
import argparse
import colorsys
from datetime import datetime
from dotenv import load_dotenv

# Add execution/ to path for reusing shared utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'execution'))

load_dotenv()

DEFAULT_BRIEF = {
    "brand_name": "",
    "tagline": "",
    "industry": "",
    "target_audience": "",
    "brand_colors": {
        "primary": "#1A1A2E",
        "secondary": "#16213E",
        "accent": "#E94560",
        "text_light": "#FFFFFF",
        "text_dark": "#1A1A2E",
        "background": "#F5F5F5"
    },
    "fonts": {
        "heading": "Inter",
        "body": "Inter"
    },
    "logo_path": "",
    "hero_images": [],
    "offers": [],
    "cta_text": "Learn More",
    "website_url": "",
    "ad_requests": []
}

AVAILABLE_TEMPLATES = {
    "carousel": ["hook_problem_cta", "listicle", "before_after", "testimonial", "educational"],
    "single": ["hero_offer", "social_proof", "product_feature"]
}


def hex_to_hsl(hex_color):
    """Convert hex color to HSL tuple."""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h * 360, s * 100, l * 100


def hsl_to_hex(h, s, l):
    """Convert HSL values to hex color string."""
    r, g, b = colorsys.hls_to_rgb(h / 360.0, l / 100.0, s / 100.0)
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"


def generate_secondary(primary_hex):
    """Generate a darker shade of the primary color."""
    h, s, l = hex_to_hsl(primary_hex)
    return hsl_to_hex(h, s, max(l - 15, 5))


def generate_accent(primary_hex):
    """Generate a complementary accent color."""
    h, s, l = hex_to_hsl(primary_hex)
    accent_h = (h + 150) % 360
    return hsl_to_hex(accent_h, min(s + 20, 100), min(l + 10, 60))


def auto_fill_colors(colors):
    """Fill in missing colors based on the primary color."""
    primary = colors.get("primary", "#1A1A2E")

    if not colors.get("secondary"):
        colors["secondary"] = generate_secondary(primary)
    if not colors.get("accent"):
        colors["accent"] = generate_accent(primary)
    if not colors.get("text_light"):
        colors["text_light"] = "#FFFFFF"
    if not colors.get("text_dark"):
        colors["text_dark"] = "#1A1A2E"
    if not colors.get("background"):
        colors["background"] = "#F5F5F5"

    return colors


def extract_colors_from_html(soup):
    """Extract brand colors from HTML page."""
    colors = {}

    # 1. Check meta theme-color
    theme_meta = soup.find('meta', attrs={'name': 'theme-color'})
    if theme_meta and theme_meta.get('content'):
        colors['primary'] = theme_meta['content']
        return colors

    # 2. Check msapplication-TileColor
    tile_meta = soup.find('meta', attrs={'name': 'msapplication-TileColor'})
    if tile_meta and tile_meta.get('content'):
        colors['primary'] = tile_meta['content']
        return colors

    # 3. Scan all style tags and inline styles for hex colors
    hex_pattern = re.compile(r'#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b')
    all_hex = []

    for style_tag in soup.find_all('style'):
        if style_tag.string:
            all_hex.extend(hex_pattern.findall(style_tag.string))

    for tag in soup.find_all(style=True):
        all_hex.extend(hex_pattern.findall(tag['style']))

    # Filter out common non-brand colors (black, white, greys)
    skip = {'#000', '#000000', '#fff', '#ffffff', '#333', '#333333',
            '#666', '#666666', '#999', '#999999', '#ccc', '#cccccc',
            '#eee', '#eeeeee', '#f5f5f5', '#fafafa', '#ddd', '#dddddd'}

    brand_colors = [c.lower() for c in all_hex if c.lower() not in skip]

    if brand_colors:
        # Most frequent non-neutral color is likely the brand color
        from collections import Counter
        freq = Counter(brand_colors)
        colors['primary'] = freq.most_common(1)[0][0]
        # Normalize 3-char hex to 6-char
        if len(colors['primary']) == 4:
            c = colors['primary']
            colors['primary'] = f"#{c[1]*2}{c[2]*2}{c[3]*2}"

    return colors


def extract_logo_url(soup, base_url):
    """Try to find logo URL from page HTML."""
    from urllib.parse import urljoin

    # Check common logo patterns
    for selector in [
        soup.find('img', class_=re.compile(r'logo', re.I)),
        soup.find('img', id=re.compile(r'logo', re.I)),
        soup.find('img', alt=re.compile(r'logo', re.I)),
        soup.find('link', rel='icon'),
        soup.find('link', rel='apple-touch-icon'),
    ]:
        if selector:
            src = selector.get('src') or selector.get('href')
            if src:
                return urljoin(base_url, src)

    return ""


def extract_text_context(soup):
    """Extract useful text context from a webpage for brand understanding."""
    texts = {}

    # Title
    title = soup.find('title')
    if title:
        texts['title'] = title.get_text(strip=True)

    # Meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc:
        texts['description'] = meta_desc.get('content', '')

    # OG tags
    og_title = soup.find('meta', property='og:title')
    if og_title:
        texts['og_title'] = og_title.get('content', '')

    og_desc = soup.find('meta', property='og:description')
    if og_desc:
        texts['og_description'] = og_desc.get('content', '')

    # H1
    h1 = soup.find('h1')
    if h1:
        texts['h1'] = h1.get_text(strip=True)

    # First few paragraphs
    paras = soup.find_all('p')
    texts['paragraphs'] = [p.get_text(strip=True) for p in paras[:5] if p.get_text(strip=True)]

    return texts


def parse_from_json(json_path):
    """Parse brief from a JSON file."""
    with open(json_path, 'r') as f:
        data = json.load(f)

    brief = {**DEFAULT_BRIEF, **data}

    # Merge nested dicts properly
    if 'brand_colors' in data:
        brief['brand_colors'] = {**DEFAULT_BRIEF['brand_colors'], **data['brand_colors']}
    if 'fonts' in data:
        brief['fonts'] = {**DEFAULT_BRIEF['fonts'], **data['fonts']}

    brief['brand_colors'] = auto_fill_colors(brief['brand_colors'])
    return brief


def parse_from_url(url):
    """Parse brief by scraping a website URL."""
    from scrape_client_visuals import get_soup, download_file

    print(f"Scraping {url}...")
    soup = get_soup(url)
    if not soup:
        print("Error: Could not fetch website", file=sys.stderr)
        sys.exit(1)

    brief = {**DEFAULT_BRIEF}
    brief['website_url'] = url

    # Extract text context
    text_ctx = extract_text_context(soup)
    brief['brand_name'] = text_ctx.get('og_title', text_ctx.get('title', '')).split('|')[0].split('-')[0].strip()
    brief['tagline'] = text_ctx.get('description', text_ctx.get('og_description', ''))

    # Extract colors
    colors = extract_colors_from_html(soup)
    brief['brand_colors'] = {**DEFAULT_BRIEF['brand_colors'], **colors}
    brief['brand_colors'] = auto_fill_colors(brief['brand_colors'])

    # Download assets
    asset_dir = ".tmp/client_assets"
    os.makedirs(asset_dir, exist_ok=True)

    # Try to get logo
    logo_url = extract_logo_url(soup, url)
    if logo_url:
        logo_path = download_file(logo_url, asset_dir)
        if logo_path:
            brief['logo_path'] = logo_path

    # Download hero images
    from urllib.parse import urljoin
    img_tags = soup.find_all('img')
    hero_count = 0
    for img in img_tags[:20]:
        src = img.get('src') or img.get('data-src')
        if src and hero_count < 5:
            full_url = urljoin(url, src)
            path = download_file(full_url, asset_dir)
            if path:
                brief['hero_images'].append(path)
                hero_count += 1

    print(f"  Brand: {brief['brand_name']}")
    print(f"  Primary color: {brief['brand_colors']['primary']}")
    print(f"  Assets downloaded: {len(brief['hero_images'])} images")

    return brief


def parse_from_prompt(prompt_text):
    """Parse brief from a free-form text prompt using Claude."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY required for prompt mode", file=sys.stderr)
        sys.exit(1)

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    system_prompt = """You extract structured brand information from text descriptions.
Return ONLY valid JSON matching this schema — no markdown, no explanation:
{
  "brand_name": "string",
  "tagline": "string or empty",
  "industry": "string or empty",
  "target_audience": "string or empty",
  "brand_colors": {
    "primary": "#hex (best guess from description, or a professional default for the industry)"
  },
  "offers": ["array of offer strings mentioned, or empty array"],
  "cta_text": "string (infer from context, default: Learn More)"
}
Fill in what you can infer. Use professional color defaults for the industry if no colors mentioned."""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1000,
        messages=[{"role": "user", "content": f"Extract brand info from this description:\n\n{prompt_text}"}],
        system=system_prompt
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = re.sub(r'^```[a-z]*\n?', '', text)
        text = re.sub(r'\n?```\s*$', '', text)

    try:
        extracted = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"Error: Claude returned invalid JSON: {e}", file=sys.stderr)
        print(f"Raw response: {text[:500]}", file=sys.stderr)
        sys.exit(1)

    brief = {**DEFAULT_BRIEF, **extracted}

    if 'brand_colors' in extracted:
        brief['brand_colors'] = {**DEFAULT_BRIEF['brand_colors'], **extracted['brand_colors']}

    brief['brand_colors'] = auto_fill_colors(brief['brand_colors'])
    return brief


def ensure_ad_requests(brief):
    """If no ad_requests specified, generate sensible defaults."""
    if brief.get('ad_requests'):
        return brief

    dimensions = "1080x1080"
    brief['ad_requests'] = [
        {
            "type": "carousel",
            "template": "hook_problem_cta",
            "topic": f"Why {brief.get('target_audience', 'customers')} choose {brief.get('brand_name', 'us')}",
            "dimensions": dimensions
        },
        {
            "type": "single",
            "template": "hero_offer",
            "topic": brief.get('tagline') or f"{brief.get('brand_name', 'Brand')} — {brief.get('offers', [''])[0] if brief.get('offers') else 'Get Started'}",
            "dimensions": dimensions
        }
    ]

    return brief


def main():
    parser = argparse.ArgumentParser(
        description="Parse ad brief from JSON, URL, or text prompt",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python parse_ad_brief.py --json brief.json --output .tmp/ad_brief.json
  python parse_ad_brief.py --url "https://example.com" --output .tmp/ad_brief.json
  python parse_ad_brief.py --prompt "SaaS company called Acme, blue brand" --output .tmp/ad_brief.json"""
    )
    parser.add_argument("--json", help="Path to structured brand kit JSON")
    parser.add_argument("--url", help="Website URL to scrape for brand info")
    parser.add_argument("--prompt", help="Free-form text description of the brand")
    parser.add_argument("--output", "-o", default=".tmp/ad_brief.json", help="Output path (default: .tmp/ad_brief.json)")

    args = parser.parse_args()

    if not any([args.json, args.url, args.prompt]):
        parser.error("Provide one of: --json, --url, or --prompt")

    # Parse based on input mode
    if args.json:
        print(f"Parsing brief from JSON: {args.json}")
        brief = parse_from_json(args.json)
    elif args.url:
        brief = parse_from_url(args.url)
    elif args.prompt:
        print("Parsing brief from text prompt via Claude...")
        brief = parse_from_prompt(args.prompt)

    # Ensure ad requests exist
    brief = ensure_ad_requests(brief)

    # Validate
    if not brief.get('brand_name'):
        print("Warning: No brand_name detected. Set manually in the output JSON.", file=sys.stderr)

    # Save
    os.makedirs(os.path.dirname(args.output) or '.tmp', exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(brief, f, indent=2)

    print(f"\nAd brief saved to {args.output}")
    print(f"  Brand: {brief.get('brand_name', 'Unknown')}")
    print(f"  Colors: primary={brief['brand_colors']['primary']}, accent={brief['brand_colors']['accent']}")
    print(f"  Ad requests: {len(brief.get('ad_requests', []))}")


if __name__ == "__main__":
    main()
