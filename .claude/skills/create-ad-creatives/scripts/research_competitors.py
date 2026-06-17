#!/usr/bin/env python3
"""
Optional competitor research step for ad creative generation.

Scrapes competitor websites and analyzes ad/content patterns to inform
creative direction. Uses Claude with extended thinking for deep analysis.

Usage:
    python .claude/skills/create-ad-creatives/scripts/research_competitors.py \
        --competitors "competitor1.com,competitor2.com" \
        --brief .tmp/ad_brief.json \
        --output .tmp/competitor_research.json
"""

import os
import sys
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'execution'))

load_dotenv()


def scrape_competitor_content(urls):
    """Scrape text content and visual patterns from competitor websites."""
    from scrape_client_visuals import get_soup

    results = []
    for url in urls:
        if not url.startswith('http'):
            url = f"https://{url}"

        print(f"  Scraping {url}...")
        soup = get_soup(url)
        if not soup:
            print(f"    Failed to fetch {url}")
            continue

        # Extract useful content
        data = {'url': url}

        # Title and meta
        title = soup.find('title')
        data['title'] = title.get_text(strip=True) if title else ''

        meta_desc = soup.find('meta', attrs={'name': 'description'})
        data['description'] = meta_desc.get('content', '') if meta_desc else ''

        # Headlines
        headings = []
        for tag in ['h1', 'h2', 'h3']:
            for h in soup.find_all(tag)[:5]:
                headings.append(h.get_text(strip=True))
        data['headings'] = headings

        # CTA buttons (look for common patterns)
        ctas = []
        for btn in soup.find_all(['a', 'button'], class_=True):
            text = btn.get_text(strip=True)
            if text and len(text) < 30:
                classes = ' '.join(btn.get('class', []))
                if any(kw in classes.lower() for kw in ['btn', 'button', 'cta', 'action']):
                    ctas.append(text)
        data['ctas'] = list(set(ctas))[:10]

        # Color extraction
        import re
        hex_pattern = re.compile(r'#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b')
        all_hex = []
        for style_tag in soup.find_all('style'):
            if style_tag.string:
                all_hex.extend(hex_pattern.findall(style_tag.string))

        skip = {'#000', '#000000', '#fff', '#ffffff', '#333', '#333333',
                '#666', '#666666', '#999', '#999999', '#ccc', '#cccccc',
                '#eee', '#eeeeee', '#f5f5f5', '#fafafa'}
        brand_colors = [c.lower() for c in all_hex if c.lower() not in skip]

        from collections import Counter
        if brand_colors:
            data['colors'] = [c for c, _ in Counter(brand_colors).most_common(5)]
        else:
            data['colors'] = []

        results.append(data)

    return results


def analyze_competitors(scraped_data, brief):
    """Use Claude to analyze competitor patterns and generate recommendations."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY required", file=sys.stderr)
        sys.exit(1)

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    # Build analysis prompt
    competitor_summary = json.dumps(scraped_data, indent=2)[:8000]

    prompt = f"""Analyze these competitor websites and extract ad creative patterns.

COMPETITORS:
{competitor_summary}

OUR BRAND:
- Name: {brief.get('brand_name', 'Unknown')}
- Industry: {brief.get('industry', 'Unknown')}
- Target audience: {brief.get('target_audience', 'Unknown')}

ANALYZE AND RETURN JSON:
{{
  "best_hooks": ["5-8 scroll-stopping hooks inspired by competitor messaging but differentiated for our brand"],
  "visual_style_notes": "Description of competitor visual patterns (dark/light, text-heavy vs image-heavy, common layouts)",
  "recommended_templates": ["2-3 carousel template names from: hook_problem_cta, listicle, before_after, testimonial, educational"],
  "cta_patterns": ["Common CTA phrases used by competitors"],
  "color_insights": "Notes on competitor color usage and how to differentiate",
  "messaging_gaps": "What competitors are NOT saying that we could leverage",
  "recommended_angles": ["3-5 content angles that would differentiate from competitors"]
}}

Return ONLY valid JSON."""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        import re
        text = re.sub(r'^```[a-z]*\n?', '', text)
        text = re.sub(r'\n?```\s*$', '', text)

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"Error: Claude returned invalid JSON: {e}", file=sys.stderr)
        print(f"Raw response: {text[:500]}", file=sys.stderr)
        return {
            "best_hooks": [],
            "visual_style_notes": "Analysis failed - review raw data manually",
            "recommended_templates": ["hook_problem_cta"],
            "cta_patterns": [],
            "color_insights": "",
            "messaging_gaps": "",
            "recommended_angles": []
        }


def main():
    parser = argparse.ArgumentParser(
        description="Research competitor ad patterns for creative inspiration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python research_competitors.py --competitors "competitor1.com,competitor2.com" --brief .tmp/ad_brief.json
  python research_competitors.py --competitors "https://acme.com" --brief .tmp/ad_brief.json --output .tmp/research.json"""
    )
    parser.add_argument("--competitors", "-c", required=True, help="Comma-separated competitor URLs")
    parser.add_argument("--brief", "-b", required=True, help="Ad brief JSON path")
    parser.add_argument("--output", "-o", default=".tmp/competitor_research.json", help="Output path")

    args = parser.parse_args()

    # Parse competitor URLs
    urls = [u.strip() for u in args.competitors.split(',') if u.strip()]
    if not urls:
        print("Error: No competitor URLs provided", file=sys.stderr)
        sys.exit(1)

    with open(args.brief, 'r') as f:
        brief = json.load(f)

    print(f"Researching {len(urls)} competitors...")

    # Scrape
    scraped = scrape_competitor_content(urls)
    if not scraped:
        print("Error: Could not scrape any competitor sites", file=sys.stderr)
        sys.exit(1)

    print(f"  Scraped {len(scraped)} sites successfully")

    # Analyze
    print("Analyzing patterns with Claude...")
    analysis = analyze_competitors(scraped, brief)

    # Combine
    output = {
        'generated_at': datetime.now().isoformat(),
        'competitors_analyzed': len(scraped),
        'raw_data': scraped,
        'analysis': analysis
    }

    os.makedirs(os.path.dirname(args.output) or '.tmp', exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nResearch saved to {args.output}")
    print(f"  Hooks found: {len(analysis.get('best_hooks', []))}")
    print(f"  Recommended templates: {', '.join(analysis.get('recommended_templates', []))}")
    print(f"  Content angles: {len(analysis.get('recommended_angles', []))}")


if __name__ == "__main__":
    main()
