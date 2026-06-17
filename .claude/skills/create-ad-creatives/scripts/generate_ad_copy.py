#!/usr/bin/env python3
"""
Generate ad copy variations for carousel and single-image ads using Claude.

Produces per-slide headlines, body text, and CTAs for each ad request in the brief.
Follows the parallel generation pattern from generate_instagram_copy.py.

Usage:
    python .claude/skills/create-ad-creatives/scripts/generate_ad_copy.py --brief .tmp/ad_brief.json --output .tmp/ad_copy.json
    python .claude/skills/create-ad-creatives/scripts/generate_ad_copy.py --brief .tmp/ad_brief.json --variations 3 --workers 3
"""

import os
import sys
import json
import argparse
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import anthropic

load_dotenv()

MAX_RETRIES = 3
DEFAULT_WORKERS = 3
DEFAULT_VARIATIONS = 2

# Template-specific slide structures
CAROUSEL_STRUCTURES = {
    "hook_problem_cta": {
        "slide_count": 5,
        "slides": [
            {"type": "hook", "instruction": "Bold provocative question or statement that stops the scroll. Max 8 words."},
            {"type": "problem", "instruction": "First pain point the audience faces. Headline max 6 words, body 1-2 sentences."},
            {"type": "problem", "instruction": "Second pain point or consequence. Headline max 6 words, body 1-2 sentences."},
            {"type": "solution", "instruction": "How the brand solves it. Headline max 6 words, body 1-2 sentences."},
            {"type": "cta", "instruction": "Clear call to action with the offer. Headline is the CTA text, body is supporting urgency line."}
        ]
    },
    "listicle": {
        "slide_count": 6,
        "slides": [
            {"type": "hook", "instruction": "Number + topic hook (e.g. '5 Ways to...'). Max 8 words."},
            {"type": "list_item", "instruction": "Tip #1 — concise, actionable. Headline max 6 words, body 1 sentence."},
            {"type": "list_item", "instruction": "Tip #2 — concise, actionable. Headline max 6 words, body 1 sentence."},
            {"type": "list_item", "instruction": "Tip #3 — concise, actionable. Headline max 6 words, body 1 sentence."},
            {"type": "list_item", "instruction": "Tip #4 — concise, actionable. Headline max 6 words, body 1 sentence."},
            {"type": "cta", "instruction": "CTA slide. Headline is the action, body is the offer or benefit."}
        ]
    },
    "before_after": {
        "slide_count": 5,
        "slides": [
            {"type": "hook", "instruction": "Split 'Before vs After' hook. Bold, contrasting. Max 6 words."},
            {"type": "before", "instruction": "The painful 'before' state. Headline max 6 words, body describes the struggle."},
            {"type": "bridge", "instruction": "The transition moment ('Then we discovered...'). Headline max 6 words, body is the turning point."},
            {"type": "after", "instruction": "The transformed 'after' state. Headline max 6 words, body shows the result with specifics."},
            {"type": "cta", "instruction": "CTA with the transformation promise. Headline is the CTA, body is social proof or urgency."}
        ]
    },
    "testimonial": {
        "slide_count": 5,
        "slides": [
            {"type": "hook", "instruction": "Most compelling quote excerpt in quotation marks. Max 12 words."},
            {"type": "context", "instruction": "Customer's situation/context before. Headline: customer name & title, body: their challenge."},
            {"type": "challenge", "instruction": "The specific problem they faced. Headline max 6 words, body: the impact."},
            {"type": "result", "instruction": "Key metric or outcome in massive headline (e.g. '327% increase'). Body: supporting detail."},
            {"type": "cta", "instruction": "'Want the same results?' CTA. Headline is the CTA, body is the offer."}
        ]
    },
    "educational": {
        "slide_count": 6,
        "slides": [
            {"type": "hook", "instruction": "Framework/method name as hook (e.g. 'The ABC Framework'). Max 8 words."},
            {"type": "step", "instruction": "Step 1 of the framework. Headline: step name, body: brief explanation."},
            {"type": "step", "instruction": "Step 2 of the framework. Headline: step name, body: brief explanation."},
            {"type": "step", "instruction": "Step 3 of the framework. Headline: step name, body: brief explanation."},
            {"type": "step", "instruction": "Step 4 of the framework. Headline: step name, body: brief explanation."},
            {"type": "cta", "instruction": "'Ready to implement?' CTA. Headline is the CTA, body is the resource/offer."}
        ]
    }
}

SINGLE_STRUCTURES = {
    "hero_offer": {
        "instruction": "Hero offer ad with bold headline (max 8 words), subheadline (max 15 words), and CTA button text (max 4 words)."
    },
    "social_proof": {
        "instruction": "Social proof ad with a customer quote (max 25 words), customer name + title, star rating (1-5), and a subtle CTA (max 4 words)."
    },
    "product_feature": {
        "instruction": "Product feature ad with feature headline (max 6 words), 3-4 bullet points (max 8 words each), and CTA button text (max 4 words)."
    }
}


def build_carousel_prompt(ad_request, brief, structure, variation_num, total_variations):
    """Build the Claude prompt for a carousel ad."""
    slides_desc = "\n".join(
        f"  Slide {i+1} ({s['type']}): {s['instruction']}"
        for i, s in enumerate(structure['slides'])
    )

    return f"""Generate ad copy variation {variation_num} of {total_variations} for a {structure['slide_count']}-slide carousel ad.

BRAND:
- Name: {brief.get('brand_name', 'Brand')}
- Tagline: {brief.get('tagline', '')}
- Industry: {brief.get('industry', '')}

AUDIENCE: {brief.get('target_audience', 'General audience')}
TOPIC: {ad_request.get('topic', '')}
OFFER: {', '.join(brief.get('offers', [])) or 'None specified'}
DEFAULT CTA: {brief.get('cta_text', 'Learn More')}

SLIDE STRUCTURE:
{slides_desc}

RULES:
- Headlines must be SHORT and punchy (see max word counts above)
- Body text max 2 sentences per slide
- Make it feel different from other variations (vary hooks, angles, word choice)
- No emojis
- CTA slide must include the offer if one exists

Return ONLY valid JSON:
{{
  "slides": [
    {{"slide_num": 1, "type": "hook", "headline": "...", "body": "", "cta": ""}},
    {{"slide_num": 2, "type": "problem", "headline": "...", "body": "...", "cta": ""}},
    ...
  ],
  "primary_text": "Caption text for the post (2-3 sentences with hook + value + CTA)",
  "hashtags": "#relevant #hashtags #here"
}}"""


def build_single_prompt(ad_request, brief, structure, variation_num, total_variations):
    """Build the Claude prompt for a single-image ad."""
    template = ad_request.get('template', 'hero_offer')

    return f"""Generate ad copy variation {variation_num} of {total_variations} for a single-image {template} ad.

BRAND:
- Name: {brief.get('brand_name', 'Brand')}
- Tagline: {brief.get('tagline', '')}
- Industry: {brief.get('industry', '')}

AUDIENCE: {brief.get('target_audience', 'General audience')}
TOPIC: {ad_request.get('topic', '')}
OFFER: {', '.join(brief.get('offers', [])) or 'None specified'}
DEFAULT CTA: {brief.get('cta_text', 'Learn More')}

AD TYPE: {structure['instruction']}

RULES:
- Be concise — this is a single image, not a carousel
- Make it feel different from other variations
- No emojis

Return ONLY valid JSON:
{{
  "headline": "Main headline text",
  "subheadline": "Supporting subheadline (if applicable)",
  "body": "Body text or bullet points",
  "cta": "CTA button text",
  "primary_text": "Caption text for the post (2-3 sentences)",
  "hashtags": "#relevant #hashtags"
}}"""


def generate_copy_for_ad(ad_index, ad_request, brief, anthropic_client, num_variations=2, retry_count=0):
    """Generate copy variations for a single ad request."""
    ad_type = ad_request.get('type', 'carousel')
    template = ad_request.get('template', 'hook_problem_cta' if ad_type == 'carousel' else 'hero_offer')

    variations = []

    for v in range(1, num_variations + 1):
        if ad_type == 'carousel':
            structure = CAROUSEL_STRUCTURES.get(template, CAROUSEL_STRUCTURES['hook_problem_cta'])
            prompt = build_carousel_prompt(ad_request, brief, structure, v, num_variations)
        else:
            structure = SINGLE_STRUCTURES.get(template, SINGLE_STRUCTURES['hero_offer'])
            prompt = build_single_prompt(ad_request, brief, structure, v, num_variations)

        for attempt in range(MAX_RETRIES):
            try:
                response = anthropic_client.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )

                text = response.content[0].text.strip()
                if text.startswith("```"):
                    import re as _re
                    text = _re.sub(r'^```[a-z]*\n?', '', text)
                    text = _re.sub(r'\n?```\s*$', '', text)

                parsed = json.loads(text)
                parsed['variation'] = v
                variations.append(parsed)
                break

            except anthropic.RateLimitError:
                wait = (2 ** attempt) * 2
                print(f"    Ad {ad_index} v{v} rate limited, retrying in {wait}s...")
                time.sleep(wait)
            except json.JSONDecodeError:
                print(f"    Ad {ad_index} v{v} JSON parse error, retrying...")
                time.sleep(2)
            except Exception as e:
                print(f"    Ad {ad_index} v{v} error: {str(e)[:60]}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2)

    return {
        "ad_index": ad_index,
        "type": ad_type,
        "template": template,
        "topic": ad_request.get('topic', ''),
        "dimensions": ad_request.get('dimensions', '1080x1080'),
        "variations": variations
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate ad copy variations using Claude",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python generate_ad_copy.py --brief .tmp/ad_brief.json --output .tmp/ad_copy.json
  python generate_ad_copy.py --brief .tmp/ad_brief.json --variations 3 --workers 3"""
    )
    parser.add_argument("--brief", "-b", required=True, help="Ad brief JSON path")
    parser.add_argument("--research", "-r", help="Competitor research JSON (optional, enriches prompts)")
    parser.add_argument("--variations", "-v", type=int, default=DEFAULT_VARIATIONS, help=f"Variations per ad (default: {DEFAULT_VARIATIONS})")
    parser.add_argument("--workers", "-w", type=int, default=DEFAULT_WORKERS, help=f"Parallel workers (default: {DEFAULT_WORKERS})")
    parser.add_argument("--output", "-o", help="Output file (default: .tmp/ad_copy_TIMESTAMP.json)")

    args = parser.parse_args()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)

    # Load brief
    with open(args.brief, 'r') as f:
        brief = json.load(f)

    ad_requests = brief.get('ad_requests', [])
    if not ad_requests:
        print("Error: No ad_requests in brief", file=sys.stderr)
        sys.exit(1)

    print(f"Generating {args.variations} copy variations for {len(ad_requests)} ads with {args.workers} workers...")

    anthropic_client = anthropic.Anthropic(api_key=api_key)

    # Process in parallel
    all_copy = [None] * len(ad_requests)
    completed = 0

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_idx = {
            executor.submit(
                generate_copy_for_ad, i, req, brief, anthropic_client, args.variations
            ): i
            for i, req in enumerate(ad_requests)
        }

        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                result = future.result()
                all_copy[idx] = result
                completed += 1
                num_vars = len(result.get('variations', []))
                print(f"  [{completed}/{len(ad_requests)}] Ad {idx} ({result['template']}): {num_vars} variations")
            except Exception as e:
                completed += 1
                all_copy[idx] = {
                    "ad_index": idx,
                    "type": ad_requests[idx].get('type', ''),
                    "template": ad_requests[idx].get('template', ''),
                    "topic": ad_requests[idx].get('topic', ''),
                    "dimensions": ad_requests[idx].get('dimensions', '1080x1080'),
                    "variations": []
                }
                print(f"  [{completed}/{len(ad_requests)}] Ad {idx}: FAILED - {e}")

    # Stats
    total_vars = sum(len(c.get('variations', [])) for c in all_copy if c)
    failed = sum(1 for c in all_copy if c and not c.get('variations'))
    print(f"\nGenerated {total_vars} total copy variations")
    if failed:
        print(f"Failed ads: {failed}")

    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = args.output or f".tmp/ad_copy_{timestamp}.json"
    os.makedirs(os.path.dirname(output_path) or '.tmp', exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(all_copy, f, indent=2)

    print(f"Ad copy saved to {output_path}")


if __name__ == "__main__":
    main()
