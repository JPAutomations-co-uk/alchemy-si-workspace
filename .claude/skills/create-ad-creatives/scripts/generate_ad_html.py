#!/usr/bin/env python3
"""
Generate ad creatives as HTML files by injecting copy + brand into templates.

Reads ad brief and copy JSON, selects appropriate HTML templates, injects brand
colors, fonts, copy text, and logo, then outputs self-contained HTML files ready
for screenshotting via Playwright.

Usage:
    python .claude/skills/create-ad-creatives/scripts/generate_ad_html.py --brief .tmp/ad_brief.json --copy .tmp/ad_copy.json --output .tmp/ad_html/
    python .claude/skills/create-ad-creatives/scripts/generate_ad_html.py --brief .tmp/ad_brief.json --copy .tmp/ad_copy.json --flux-backgrounds --output .tmp/ad_html/
"""

import os
import sys
import json
import base64
import argparse
import urllib.parse
from html import escape
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'execution'))

load_dotenv()

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), '..', 'templates')


def load_template(template_name):
    """Load an HTML template file."""
    path = os.path.join(TEMPLATES_DIR, f"{template_name}.html")
    if not os.path.exists(path):
        print(f"Error: Template not found: {path}", file=sys.stderr)
        return None
    with open(path, 'r') as f:
        return f.read()


def encode_logo(logo_path):
    """Base64 encode a logo image for embedding in HTML."""
    if not logo_path or not os.path.exists(logo_path):
        return ""
    try:
        ext = os.path.splitext(logo_path)[1].lower()
        mime = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                '.svg': 'image/svg+xml', '.webp': 'image/webp'}.get(ext, 'image/png')
        with open(logo_path, 'rb') as f:
            data = base64.b64encode(f.read()).decode('utf-8')
        return f'data:{mime};base64,{data}'
    except Exception:
        return ""


def parse_dimensions(dim_str):
    """Parse '1080x1080' into (width, height) tuple."""
    try:
        parts = dim_str.lower().split('x')
        return int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        return 1080, 1080


def build_slide_indicator(current, total, is_dark_bg=True):
    """Build HTML for slide position indicator dots."""
    dots = []
    for i in range(1, total + 1):
        cls = "dot active" if i == current else "dot"
        dots.append(f'<span class="{cls}"></span>')
    return f'<div class="slide-indicator">{"".join(dots)}</div>'


def validate_hex_color(color, default='#1A1A2E'):
    """Validate a hex color string to prevent CSS injection."""
    import re
    if color and re.match(r'^#[0-9a-fA-F]{3,6}$', color):
        return color
    return default


def get_brand_vars(brief):
    """Extract common template variables from the brief."""
    colors = brief.get('brand_colors', {})
    fonts = brief.get('fonts', {})
    heading_font = fonts.get('heading', 'Inter')
    body_font = fonts.get('body', 'Inter')

    return {
        'primary_color': validate_hex_color(colors.get('primary'), '#1A1A2E'),
        'secondary_color': validate_hex_color(colors.get('secondary'), '#16213E'),
        'accent_color': validate_hex_color(colors.get('accent'), '#E94560'),
        'text_light': validate_hex_color(colors.get('text_light'), '#FFFFFF'),
        'text_dark': validate_hex_color(colors.get('text_dark'), '#1A1A2E'),
        'bg_color': validate_hex_color(colors.get('background'), '#F5F5F5'),
        'heading_font': heading_font,
        'body_font': body_font,
        'heading_font_encoded': urllib.parse.quote(heading_font),
        'body_font_encoded': urllib.parse.quote(body_font),
        'brand_name': escape(brief.get('brand_name', '')),
    }


def build_logo_html(brief):
    """Build logo img tag or empty string."""
    logo_b64 = encode_logo(brief.get('logo_path', ''))
    if logo_b64:
        return f'<img class="logo" src="{logo_b64}" alt="Logo">'
    return ""


def encode_hero_image(image_path):
    """Base64 encode a hero/background image for embedding in HTML."""
    if not image_path or not os.path.exists(image_path):
        return ""
    try:
        ext = os.path.splitext(image_path)[1].lower()
        mime = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                '.webp': 'image/webp', '.gif': 'image/gif'}.get(ext, 'image/jpeg')
        with open(image_path, 'rb') as f:
            data = base64.b64encode(f.read()).decode('utf-8')
        return f'data:{mime};base64,{data}'
    except Exception:
        return ""


def build_hero_image_html(brief, css_class="hero-img"):
    """Build hero image img tag or empty string. Templates use CSS fallback if empty."""
    # Check hero_images list first, then hero_image singular
    hero_images = brief.get('hero_images', [])
    hero_path = hero_images[0] if hero_images else brief.get('hero_image', '')
    hero_b64 = encode_hero_image(hero_path)
    if hero_b64:
        return f'<img class="{css_class}" src="{hero_b64}" alt="">'
    return ""


def build_generic_single(copy_data, brief, width, height, template_name, extra_vars=None):
    """Generic builder for simple single-image templates — injects copy, brand, logo, hero image."""
    template = load_template(template_name)
    if not template:
        return None
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
        return template.format(**vars_dict)
    except KeyError as e:
        print(f"  Warning: Missing template variable {e} in {template_name}", file=sys.stderr)
        return None


# ============================================================
# CAROUSEL SLIDE BUILDERS
# ============================================================

def build_hook_problem_cta_slide(slide, slide_num, total_slides, brief):
    """Build slide content for hook_problem_cta carousel."""
    slide_type = slide.get('type', 'hook')
    headline = escape(slide.get('headline', ''))
    body = escape(slide.get('body', ''))
    cta = escape(slide.get('cta', brief.get('cta_text', 'Learn More')))
    indicator = build_slide_indicator(slide_num, total_slides)
    logo = build_logo_html(brief)

    if slide_type == 'hook':
        content = f'<div class="headline">{headline}</div><div class="accent-bar"></div>{indicator}{logo}'
        return 'slide-hook', content
    elif slide_type == 'problem':
        content = f'<div class="problem-icon"></div><div class="headline">{headline}</div><div class="body">{body}</div>{indicator}{logo}'
        return 'slide-problem', content
    elif slide_type == 'solution':
        content = f'<div class="solution-icon"></div><div class="headline">{headline}</div><div class="body">{body}</div>{indicator}{logo}'
        return 'slide-solution', content
    elif slide_type == 'cta':
        content = f'<div class="headline">{headline}</div><div class="body">{body}</div><div class="cta-button">{cta}</div>{indicator}{logo}'
        return 'slide-cta', content
    else:
        content = f'<div class="headline">{headline}</div><div class="body">{body}</div>{indicator}{logo}'
        return 'slide-problem', content


def build_listicle_slide(slide, slide_num, total_slides, brief):
    """Build slide content for listicle carousel."""
    slide_type = slide.get('type', 'hook')
    headline = escape(slide.get('headline', ''))
    body = escape(slide.get('body', ''))
    cta = escape(slide.get('cta', brief.get('cta_text', 'Learn More')))
    indicator = build_slide_indicator(slide_num, total_slides)
    logo = build_logo_html(brief)

    if slide_type == 'hook':
        # Extract number from headline if possible
        import re
        num_match = re.search(r'\d+', headline)
        big_num = num_match.group() if num_match else str(total_slides - 1)
        content = f'<div class="big-number">{big_num}</div><div class="headline">{headline}</div>{indicator}{logo}'
        return 'slide-hook', content
    elif slide_type == 'list_item':
        item_num = slide.get('slide_num', slide_num)
        content = f'<div class="item-number">{item_num - 1}</div><div class="headline">{headline}</div><div class="body">{body}</div>{indicator}{logo}'
        return 'slide-list-item', content
    elif slide_type == 'cta':
        content = f'<div class="headline">{headline}</div><div class="body">{body}</div><div class="cta-button">{cta}</div>{indicator}{logo}'
        return 'slide-cta', content
    else:
        content = f'<div class="headline">{headline}</div><div class="body">{body}</div>{indicator}{logo}'
        return 'slide-list-item', content


def build_before_after_slide(slide, slide_num, total_slides, brief):
    """Build slide content for before_after carousel."""
    slide_type = slide.get('type', 'hook')
    headline = escape(slide.get('headline', ''))
    body = escape(slide.get('body', ''))
    cta = escape(slide.get('cta', brief.get('cta_text', 'Learn More')))
    indicator = build_slide_indicator(slide_num, total_slides)
    logo = build_logo_html(brief)

    if slide_type == 'hook':
        content = f'<div class="split-labels"><span class="split-label">Before</span><span class="split-label">After</span></div><div class="headline">{headline}</div>{indicator}{logo}'
        return 'slide-hook', content
    elif slide_type == 'before':
        content = f'<div class="tag">Before</div><div class="headline">{headline}</div><div class="body">{body}</div>{indicator}{logo}'
        return 'slide-before', content
    elif slide_type == 'bridge':
        content = f'<div class="headline">{headline}</div><div class="body">{body}</div>{indicator}{logo}'
        return 'slide-bridge', content
    elif slide_type == 'after':
        content = f'<div class="tag">After</div><div class="headline">{headline}</div><div class="body">{body}</div>{indicator}{logo}'
        return 'slide-after', content
    elif slide_type == 'cta':
        content = f'<div class="headline">{headline}</div><div class="body">{body}</div><div class="cta-button">{cta}</div>{indicator}{logo}'
        return 'slide-cta', content
    else:
        content = f'<div class="headline">{headline}</div><div class="body">{body}</div>{indicator}{logo}'
        return 'slide-before', content


def build_testimonial_slide(slide, slide_num, total_slides, brief):
    """Build slide content for testimonial carousel."""
    slide_type = slide.get('type', 'hook')
    headline = escape(slide.get('headline', ''))
    body = escape(slide.get('body', ''))
    cta = escape(slide.get('cta', brief.get('cta_text', 'Learn More')))
    indicator = build_slide_indicator(slide_num, total_slides)
    logo = build_logo_html(brief)

    if slide_type == 'hook':
        content = f'<div class="quote-mark">&ldquo;</div><div class="headline">{headline}</div><div class="attribution">{body}</div>{indicator}{logo}'
        return 'slide-hook', content
    elif slide_type == 'context':
        content = f'<div class="tag">Their Story</div><div class="headline">{headline}</div><div class="body">{body}</div>{indicator}{logo}'
        return 'slide-context', content
    elif slide_type == 'challenge':
        content = f'<div class="headline">{headline}</div><div class="body">{body}</div>{indicator}{logo}'
        return 'slide-challenge', content
    elif slide_type == 'result':
        content = f'<div class="headline">{headline}</div><div class="body">{body}</div>{indicator}{logo}'
        return 'slide-result', content
    elif slide_type == 'cta':
        stars = '<div class="stars">' + ('&#9733;' * 5) + '</div>'
        content = f'{stars}<div class="headline">{headline}</div><div class="body">{body}</div><div class="cta-button">{cta}</div>{indicator}{logo}'
        return 'slide-cta', content
    else:
        content = f'<div class="headline">{headline}</div><div class="body">{body}</div>{indicator}{logo}'
        return 'slide-context', content


def build_educational_slide(slide, slide_num, total_slides, brief):
    """Build slide content for educational carousel."""
    slide_type = slide.get('type', 'hook')
    headline = escape(slide.get('headline', ''))
    body = escape(slide.get('body', ''))
    cta = escape(slide.get('cta', brief.get('cta_text', 'Learn More')))
    indicator = build_slide_indicator(slide_num, total_slides)
    logo = build_logo_html(brief)

    if slide_type == 'hook':
        content = f'<div class="tag">Framework</div><div class="headline">{headline}</div><div class="body">{body}</div>{indicator}{logo}'
        return 'slide-hook', content
    elif slide_type == 'step':
        step_num = slide.get('slide_num', slide_num) - 1
        content = f'''<div class="step-number">
            <div class="step-circle">{step_num}</div>
            <div class="step-label">Step {step_num}</div>
        </div>
        <div class="headline">{headline}</div>
        <div class="body">{body}</div>
        <div class="divider"></div>{indicator}{logo}'''
        return 'slide-step', content
    elif slide_type == 'cta':
        content = f'<div class="headline">{headline}</div><div class="body">{body}</div><div class="cta-button">{cta}</div>{indicator}{logo}'
        return 'slide-cta', content
    else:
        content = f'<div class="headline">{headline}</div><div class="body">{body}</div>{indicator}{logo}'
        return 'slide-step', content


CAROUSEL_BUILDERS = {
    'hook_problem_cta': build_hook_problem_cta_slide,
    'listicle': build_listicle_slide,
    'before_after': build_before_after_slide,
    'testimonial': build_testimonial_slide,
    'educational': build_educational_slide,
}


# ============================================================
# SINGLE IMAGE BUILDERS
# ============================================================

def build_single_hero_offer(copy_data, brief, width, height):
    """Build complete HTML for hero_offer single image."""
    template = load_template('single_hero_offer')
    if not template:
        return None

    brand_vars = get_brand_vars(brief)
    logo_html = build_logo_html(brief)

    html = template.format(
        width=width,
        height=height,
        headline=escape(copy_data.get('headline', '')),
        subheadline=escape(copy_data.get('subheadline', '')),
        cta=escape(copy_data.get('cta', brief.get('cta_text', 'Learn More'))),
        logo_html=logo_html,
        **brand_vars
    )
    return html


def build_single_social_proof(copy_data, brief, width, height):
    """Build complete HTML for social_proof single image."""
    template = load_template('single_social_proof')
    if not template:
        return None

    brand_vars = get_brand_vars(brief)

    # Parse customer info from body or subheadline
    body = copy_data.get('body', '')
    parts = body.split(',') if ',' in body else body.split('\n')
    customer_name = parts[0].strip() if parts else 'Happy Customer'
    customer_title = parts[1].strip() if len(parts) > 1 else ''

    # Star rating
    stars = '&#9733;' * 5
    stars_html = stars

    html = template.format(
        width=width,
        height=height,
        headline=escape(copy_data.get('headline', '')),
        stars_html=stars_html,
        customer_name=escape(customer_name),
        customer_title=escape(customer_title),
        cta=escape(copy_data.get('cta', brief.get('cta_text', 'Learn More'))),
        **brand_vars
    )
    return html


def build_single_product_feature(copy_data, brief, width, height):
    """Build complete HTML for product_feature single image."""
    template = load_template('single_product_feature')
    if not template:
        return None

    brand_vars = get_brand_vars(brief)

    # Parse bullet points from body
    body = copy_data.get('body', '')
    if isinstance(body, list):
        bullets = body
    else:
        bullets = [b.strip().lstrip('- ').lstrip('* ') for b in body.split('\n') if b.strip()]
    if not bullets:
        bullets = [body] if body else ['Feature 1']

    features_html = ""
    for bullet in bullets[:5]:
        features_html += f'''<li class="feature-item">
            <div class="feature-check"></div>
            <span class="feature-text">{escape(bullet)}</span>
        </li>'''

    html = template.format(
        width=width,
        height=height,
        headline=escape(copy_data.get('headline', '')),
        features_html=features_html,
        cta=escape(copy_data.get('cta', brief.get('cta_text', 'Learn More'))),
        **brand_vars
    )
    return html


def build_ig_bullet_benefits(copy_data, brief, width, height):
    """Build ig_bullet_benefits — parses body into 3 bullets with SVG checks."""
    body = copy_data.get('body', '')
    if isinstance(body, list):
        bullets = body
    else:
        bullets = [b.strip().lstrip('- ').lstrip('* ') for b in body.split('\n') if b.strip()]
    if not bullets:
        bullets = ['Benefit one', 'Benefit two', 'Benefit three']
    bullets_html = ""
    for bullet in bullets[:3]:
        bullets_html += f'''<div class="benefit-row">
            <div class="check-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
            </div>
            <span class="benefit-text">{escape(bullet)}</span>
        </div>'''
    return build_generic_single(copy_data, brief, width, height, 'ig_bullet_benefits',
                                extra_vars={'bullets_html': bullets_html})


def build_ig_comparison(copy_data, brief, width, height):
    """Build ig_comparison — splits body lines into without/with columns."""
    body = copy_data.get('body', '')
    lines = [l.strip() for l in body.split('\n') if l.strip()] if body else []
    without_items = lines[:3] if lines else ['Wasted time', 'Higher costs', 'Inconsistent results']
    with_items = lines[3:6] if len(lines) > 3 else ['Saved hours', 'Lower costs', 'Reliable results']
    without_rows = ''.join(f'<div class="comp-row comp-row-without">{escape(i)}</div>' for i in without_items)
    with_rows = ''.join(f'<div class="comp-row comp-row-with">{escape(i)}</div>' for i in with_items)
    col_html = f'''<div class="col-without">
        <div class="col-header-without">Without Us</div>
        <div class="col-body-without">{without_rows}</div>
    </div>
    <div class="col-with">
        <div class="col-header-with">With Us</div>
        <div class="col-body-with">{with_rows}</div>
    </div>'''
    return build_generic_single(copy_data, brief, width, height, 'ig_comparison',
                                extra_vars={'comparison_cols_html': col_html})


def build_ig_testimonial(copy_data, brief, width, height):
    """Build ig_testimonial — parses customer name/title from body."""
    body = copy_data.get('body', '')
    parts = [p.strip() for p in body.split(',')]
    customer_name = parts[0] if parts else 'Happy Client'
    customer_title = parts[1] if len(parts) > 1 else ''
    return build_generic_single(copy_data, brief, width, height, 'ig_testimonial',
                                extra_vars={'customer_name': escape(customer_name),
                                            'customer_title': escape(customer_title)})


def build_ig_case_study(copy_data, brief, width, height):
    """Build ig_case_study — splits body into problem|solution|result rows."""
    body = copy_data.get('body', '')
    lines = [l.strip().removeprefix('- ').removeprefix('* ') for l in body.split('\n') if l.strip()]
    problem = lines[0] if lines else 'The challenge they faced'
    solution = lines[1] if len(lines) > 1 else 'How we solved it'
    result = lines[2] if len(lines) > 2 else 'The measurable outcome'
    rows_html = f'''<div class="case-row case-row-problem">
        <div class="case-row-label">Problem</div>
        <div class="case-row-text">{escape(problem)}</div>
    </div>
    <div class="case-row case-row-solution">
        <div class="case-row-label">Solution</div>
        <div class="case-row-text">{escape(solution)}</div>
    </div>
    <div class="case-row case-row-result">
        <div class="case-row-label">Result</div>
        <div class="case-row-text">{escape(result)}</div>
    </div>'''
    return build_generic_single(copy_data, brief, width, height, 'ig_case_study',
                                extra_vars={'case_rows_html': rows_html})


def _make_ig_builder(tpl_name):
    return lambda c, b, w, h: build_generic_single(c, b, w, h, tpl_name)


SINGLE_BUILDERS = {
    # Legacy generic templates
    'hero_offer': build_single_hero_offer,
    'social_proof': build_single_social_proof,
    'product_feature': build_single_product_feature,
    # Instagram — text-only
    'ig_bold_headline':  _make_ig_builder('ig_bold_headline'),
    'ig_offer_deal':     _make_ig_builder('ig_offer_deal'),
    'ig_stats_number':   _make_ig_builder('ig_stats_number'),
    'ig_pain_point':     _make_ig_builder('ig_pain_point'),
    'ig_bullet_benefits': build_ig_bullet_benefits,
    'ig_guarantee':      _make_ig_builder('ig_guarantee'),
    'ig_free_offer':     _make_ig_builder('ig_free_offer'),
    # Instagram — brand-forward
    'ig_logo_hero':      _make_ig_builder('ig_logo_hero'),
    'ig_announcement':   _make_ig_builder('ig_announcement'),
    'ig_luxury_minimal': _make_ig_builder('ig_luxury_minimal'),
    'ig_dark_premium':   _make_ig_builder('ig_dark_premium'),
    # Instagram — CTA/conversion
    'ig_strong_cta':     _make_ig_builder('ig_strong_cta'),
    'ig_countdown':      _make_ig_builder('ig_countdown'),
    'ig_contact':        _make_ig_builder('ig_contact'),
    # Instagram — photo + text
    'ig_photo_overlay':  _make_ig_builder('ig_photo_overlay'),
    'ig_split_h':        _make_ig_builder('ig_split_h'),
    'ig_split_v':        _make_ig_builder('ig_split_v'),
    'ig_photo_frame':    _make_ig_builder('ig_photo_frame'),
    'ig_angled_split':   _make_ig_builder('ig_angled_split'),
    'ig_circle_photo':   _make_ig_builder('ig_circle_photo'),
    'ig_corner_photo':   _make_ig_builder('ig_corner_photo'),
    # Instagram — complex layout
    'ig_comparison':     build_ig_comparison,
    'ig_testimonial':    build_ig_testimonial,
    'ig_results':        _make_ig_builder('ig_results'),
    'ig_case_study':     build_ig_case_study,
}


# ============================================================
# MAIN GENERATION LOGIC
# ============================================================

def generate_carousel_html(ad_copy, brief, output_dir, variation=1):
    """Generate HTML files for a carousel ad."""
    template_name = ad_copy.get('template', 'hook_problem_cta')
    template_html_name = f"carousel_{template_name}"
    template = load_template(template_html_name)
    if not template:
        print(f"  Warning: Template {template_html_name} not found, skipping")
        return []

    builder = CAROUSEL_BUILDERS.get(template_name)
    if not builder:
        print(f"  Warning: No builder for {template_name}, skipping")
        return []

    variations = ad_copy.get('variations', [])
    if not variations:
        print(f"  Warning: No copy variations for ad {ad_copy.get('ad_index', '?')}")
        return []

    # Select the requested variation
    var_idx = min(variation - 1, len(variations) - 1)
    copy_var = variations[var_idx]

    slides = copy_var.get('slides', [])
    if not slides:
        print(f"  Warning: No slides in variation {variation}")
        return []

    dims = ad_copy.get('dimensions', '1080x1080')
    width, height = parse_dimensions(dims)
    brand_vars = get_brand_vars(brief)
    total_slides = len(slides)

    output_files = []
    ad_idx = int(ad_copy.get('ad_index', 0))
    for i, slide in enumerate(slides):
        slide_num = slide.get('slide_num', i + 1)
        slide_class, slide_content = builder(slide, slide_num, total_slides, brief)

        html = template.format(
            width=width,
            height=height,
            slide_class=slide_class,
            slide_content=slide_content,
            **brand_vars
        )
        filename = f"ad_{ad_idx}_v{variation}_slide_{slide_num}.html"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w') as f:
            f.write(html)

        output_files.append({
            'filename': filename,
            'width': width,
            'height': height,
            'ad_index': ad_idx,
            'variation': variation,
            'slide_num': slide_num,
            'type': 'carousel',
            'template': template_name
        })

    return output_files


def generate_single_html(ad_copy, brief, output_dir, variation=1):
    """Generate HTML file for a single-image ad."""
    template_name = ad_copy.get('template', 'hero_offer')
    builder = SINGLE_BUILDERS.get(template_name)
    if not builder:
        print(f"  Warning: No builder for single_{template_name}, skipping")
        return []

    variations = ad_copy.get('variations', [])
    if not variations:
        return []

    var_idx = min(variation - 1, len(variations) - 1)
    copy_var = variations[var_idx]

    dims = ad_copy.get('dimensions', '1080x1080')
    width, height = parse_dimensions(dims)

    html = builder(copy_var, brief, width, height)
    if not html:
        return []

    ad_idx = int(ad_copy.get('ad_index', 0))
    filename = f"ad_{ad_idx}_v{variation}.html"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w') as f:
        f.write(html)

    return [{
        'filename': filename,
        'width': width,
        'height': height,
        'ad_index': ad_idx,
        'variation': variation,
        'slide_num': None,
        'type': 'single',
        'template': template_name
    }]


def main():
    parser = argparse.ArgumentParser(
        description="Generate ad creatives as HTML files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python generate_ad_html.py --brief .tmp/ad_brief.json --copy .tmp/ad_copy.json --output .tmp/ad_html/
  python generate_ad_html.py --brief .tmp/ad_brief.json --copy .tmp/ad_copy.json --variation 2 --output .tmp/ad_html/"""
    )
    parser.add_argument("--brief", "-b", required=True, help="Ad brief JSON path")
    parser.add_argument("--copy", "-c", required=True, help="Ad copy JSON path")
    parser.add_argument("--variation", "-v", type=int, default=1, help="Which copy variation to use (default: 1)")
    parser.add_argument("--backgrounds", help="Path to backgrounds manifest JSON (from generate_ad_backgrounds.py)")
    parser.add_argument("--output", "-o", default=".tmp/ad_html/", help="Output directory")

    args = parser.parse_args()

    # Load inputs
    with open(args.brief, 'r') as f:
        brief = json.load(f)
    with open(args.copy, 'r') as f:
        all_copy = json.load(f)

    os.makedirs(args.output, exist_ok=True)

    # Load background images if provided
    backgrounds_map = {}
    if args.backgrounds and os.path.exists(args.backgrounds):
        with open(args.backgrounds, 'r') as f:
            bg_data = json.load(f)
        for bg in bg_data.get('backgrounds', []):
            backgrounds_map[int(bg['ad_index'])] = bg['image_path']
        print(f"Loaded {len(backgrounds_map)} AI background images")

    print(f"Generating HTML creatives for {len(all_copy)} ads (variation {args.variation})...")

    manifest = []

    for ad_copy in all_copy:
        ad_type = ad_copy.get('type', 'carousel')
        template = ad_copy.get('template', '')
        ad_idx = ad_copy.get('ad_index', '?')

        # Inject generated background if available for this ad
        working_brief = brief
        try:
            ad_idx_int = int(ad_idx)
        except (ValueError, TypeError):
            ad_idx_int = None
        if ad_idx_int is not None and ad_idx_int in backgrounds_map:
            bg_path = backgrounds_map[ad_idx_int]
            if os.path.exists(bg_path):
                working_brief = {**brief, 'hero_images': [bg_path]}
                print(f"  Ad {ad_idx}: injecting AI background")

        if ad_type == 'carousel':
            files = generate_carousel_html(ad_copy, working_brief, args.output, args.variation)
        else:
            files = generate_single_html(ad_copy, working_brief, args.output, args.variation)

        manifest.extend(files)
        print(f"  Ad {ad_idx} ({template}): {len(files)} HTML files")

    # Save manifest
    manifest_path = os.path.join(args.output, 'manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"\nGenerated {len(manifest)} HTML files in {args.output}")
    print(f"Manifest saved to {manifest_path}")


if __name__ == "__main__":
    main()
