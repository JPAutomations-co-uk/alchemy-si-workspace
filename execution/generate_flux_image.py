#!/usr/bin/env python3
"""
Generate images using Flux Pro via Replicate API.

Supports single images, carousel slides, and highlight covers.
Outputs 1080x1350 (4:5) for feed posts or 1080x1920 (9:16) for stories/reels.

Usage:
    python execution/generate_flux_image.py --prompt "Modern minimalist office interior" --output .tmp/image.png
    python execution/generate_flux_image.py --prompt "..." --aspect 9:16 --output .tmp/reel_bg.png
    python execution/generate_flux_image.py --batch .tmp/image_prompts.json --output .tmp/generated_assets
"""

import os
import sys
import json
import argparse
import time
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

MAX_RETRIES = 3
DEFAULT_WORKERS = 3
DEFAULT_MODEL = "black-forest-labs/flux-pro"
REPLICATE_API_URL = "https://api.replicate.com/v1/predictions"

# Aspect ratio to pixel dimensions
ASPECT_RATIOS = {
    "4:5": (1080, 1350),   # Feed posts, carousels
    "1:1": (1080, 1080),   # Square posts
    "9:16": (1080, 1920),  # Stories, reels, highlights
    "16:9": (1920, 1080),  # Landscape
}


def _create_prediction(headers, input_params, model=DEFAULT_MODEL):
    """Try to create a prediction, with fallback to models endpoint.

    Returns the prediction dict on success. Raises on failure.
    """
    # Primary: /v1/predictions with version field
    payload = {"version": model, "input": input_params}
    resp = requests.post(REPLICATE_API_URL, json=payload, headers=headers, timeout=30)

    if resp.status_code >= 400:
        error_body = resp.text[:300]
        print(f"  API error {resp.status_code} on /v1/predictions: {error_body}", file=sys.stderr)

        # Fallback: /v1/models/{model}/predictions (no version field needed)
        if resp.status_code in (404, 422):
            fallback_url = f"https://api.replicate.com/v1/models/{model}/predictions"
            fallback_payload = {"input": input_params}
            print(f"  Retrying via models endpoint: {fallback_url}", file=sys.stderr)
            resp = requests.post(fallback_url, json=fallback_payload, headers=headers, timeout=30)
            if resp.status_code >= 400:
                error_body = resp.text[:300]
                print(f"  Fallback also failed {resp.status_code}: {error_body}", file=sys.stderr)

    resp.raise_for_status()
    return resp.json()


def generate_image(prompt, aspect_ratio="4:5", api_token=None, retry_count=0,
                   negative_prompt=None, seed=None, brand_prefix=None, model=None):
    """Generate a single image using Flux Pro via Replicate.

    Returns the image bytes on success, None on failure.
    """
    model = model or DEFAULT_MODEL

    # Prepend brand style prefix on first call only (not on retries)
    if brand_prefix and retry_count == 0:
        prompt = f"{brand_prefix}, {prompt}"

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    width, height = ASPECT_RATIOS.get(aspect_ratio, (1080, 1350))

    input_params = {
        "prompt": prompt,
        "width": width,
        "height": height,
        "num_inference_steps": 28,
        "guidance_scale": 3.5,
    }
    if negative_prompt:
        input_params["negative_prompt"] = negative_prompt
    if seed is not None:
        input_params["seed"] = seed

    try:
        # Create prediction (with fallback endpoint)
        prediction = _create_prediction(headers, input_params, model)

        pred_url = prediction.get("urls", {}).get("get")
        if not pred_url:
            print(f"  Error: No prediction URL returned. Response: {json.dumps(prediction)[:200]}")
            return None

        # Poll for completion
        for _ in range(120):  # Max 4 minutes
            time.sleep(2)
            poll = requests.get(pred_url, headers=headers, timeout=15)
            poll.raise_for_status()
            status_data = poll.json()
            status = status_data.get("status")

            if status == "succeeded":
                output = status_data.get("output")
                if isinstance(output, list):
                    output = output[0]
                if output:
                    img_resp = requests.get(output, timeout=60)
                    img_resp.raise_for_status()
                    return img_resp.content
                return None

            if status == "failed":
                error = status_data.get("error", "Unknown error")
                print(f"  Prediction failed: {error}")
                if retry_count < MAX_RETRIES:
                    time.sleep(2 ** retry_count)
                    return generate_image(prompt, aspect_ratio, api_token, retry_count + 1,
                                          negative_prompt=negative_prompt, seed=seed, model=model)
                return None

        print("  Prediction timed out after 4 minutes")
        return None

    except requests.exceptions.HTTPError as e:
        if e.response is not None:
            print(f"  HTTP {e.response.status_code}: {e.response.text[:200]}", file=sys.stderr)
        if e.response and e.response.status_code == 429:
            if retry_count < MAX_RETRIES:
                wait = (2 ** retry_count) * 3
                print(f"  Rate limited, retrying in {wait}s...")
                time.sleep(wait)
                return generate_image(prompt, aspect_ratio, api_token, retry_count + 1,
                                      negative_prompt=negative_prompt, seed=seed, model=model)
        print(f"  HTTP error: {e}")
        return None
    except Exception as e:
        print(f"  Error: {str(e)[:80]}")
        if retry_count < MAX_RETRIES:
            time.sleep(2)
            return generate_image(prompt, aspect_ratio, api_token, retry_count + 1,
                                  negative_prompt=negative_prompt, seed=seed, model=model)
        return None


def process_single(prompt, output_path, aspect_ratio, api_token,
                   negative_prompt=None, seed=None, brand_prefix=None, model=None):
    """Generate and save a single image."""
    print(f"Generating image: {prompt[:60]}...")
    img_bytes = generate_image(prompt, aspect_ratio, api_token,
                               negative_prompt=negative_prompt, seed=seed,
                               brand_prefix=brand_prefix, model=model)
    if img_bytes:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(img_bytes)
        print(f"  Saved: {output_path}")
        return True
    print(f"  FAILED: {prompt[:40]}")
    return False


def process_batch(batch_file, output_dir, api_token, workers):
    """Process a batch of image prompts from a JSON file.

    Expected JSON format (list of dicts):
    [
        {
            "id": "day1_slide1",
            "prompt": "Modern office interior with natural light",
            "aspect_ratio": "4:5",
            "filename": "day1_slide1.png"
        }
    ]
    """
    with open(batch_file, "r") as f:
        items = json.load(f)

    os.makedirs(output_dir, exist_ok=True)
    print(f"Processing {len(items)} images with {workers} workers...\n")

    results = {"succeeded": 0, "failed": 0, "skipped": 0, "outputs": []}

    def _generate_one(item):
        prompt = item.get("prompt", "")
        if not prompt:
            return None, "skipped"

        aspect = item.get("aspect_ratio", "4:5")
        filename = item.get("filename", f"{item.get('id', 'image')}.png")
        filepath = os.path.join(output_dir, filename)

        if os.path.exists(filepath):
            print(f"  Skipping existing: {filename}")
            return filepath, "skipped"

        img_bytes = generate_image(prompt, aspect, api_token)
        if img_bytes:
            with open(filepath, "wb") as f:
                f.write(img_bytes)
            return filepath, "succeeded"
        return None, "failed"

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_item = {
            executor.submit(_generate_one, item): item for item in items
        }

        for future in as_completed(future_to_item):
            item = future_to_item[future]
            try:
                filepath, status = future.result()
                results[status] += 1
                if filepath:
                    results["outputs"].append(filepath)
                label = item.get("id", item.get("filename", "?"))
                print(f"  [{results['succeeded'] + results['failed'] + results['skipped']}/{len(items)}] {label}: {status}")
            except Exception as e:
                results["failed"] += 1
                print(f"  Error: {e}")

    print(f"\nDone: {results['succeeded']} succeeded, {results['failed']} failed, {results['skipped']} skipped")
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Generate images using Flux Pro via Replicate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python execution/generate_flux_image.py --prompt "Modern office" --output .tmp/office.png
  python execution/generate_flux_image.py --prompt "..." --aspect 9:16 --output .tmp/story.png
  python execution/generate_flux_image.py --batch .tmp/prompts.json --output .tmp/images/""",
    )
    parser.add_argument("--prompt", "-p", help="Single image prompt")
    parser.add_argument("--batch", "-b", help="Batch JSON file with prompts")
    parser.add_argument("--output", "-o", required=True, help="Output file (single) or directory (batch)")
    parser.add_argument("--aspect", "-a", default="4:5", choices=list(ASPECT_RATIOS.keys()), help="Aspect ratio (default: 4:5)")
    parser.add_argument("--workers", "-w", type=int, default=DEFAULT_WORKERS, help=f"Parallel workers for batch (default: {DEFAULT_WORKERS})")
    parser.add_argument("--negative-prompt", help="Negative prompt (what to exclude from the image)")
    parser.add_argument("--brand-prefix", help="Brand style prefix to prepend to prompt")
    parser.add_argument("--seed", type=int, help="Fixed seed for reproducible results (useful for carousel coherence)")
    parser.add_argument("--template", help="Visual template name to auto-load brand prefix + negative prompt")
    parser.add_argument("--model", "-m", default=DEFAULT_MODEL,
                        help=f"Replicate model identifier (default: {DEFAULT_MODEL})")

    args = parser.parse_args()

    api_token = os.getenv("REPLICATE_API_TOKEN")
    if not api_token:
        print("Error: REPLICATE_API_TOKEN not set in .env", file=sys.stderr)
        sys.exit(1)

    # Load template if specified
    brand_prefix = args.brand_prefix
    negative_prompt = args.negative_prompt
    if args.template:
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "load_brand_template",
                os.path.join(os.path.dirname(__file__), "load_brand_template.py")
            )
            lbt = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(lbt)
            tmpl = lbt.load_template(args.template)
            if not brand_prefix:
                brand_prefix = lbt.build_flux_prefix(tmpl)
            if not negative_prompt:
                negative_prompt = lbt.build_flux_negative(tmpl)
            print(f"Template: {tmpl.get('name', args.template)}")
        except Exception as e:
            print(f"Warning: Could not load template '{args.template}': {e}")

    if args.prompt:
        success = process_single(args.prompt, args.output, args.aspect, api_token,
                                 negative_prompt=negative_prompt, seed=args.seed,
                                 brand_prefix=brand_prefix, model=args.model)
        sys.exit(0 if success else 1)
    elif args.batch:
        results = process_batch(args.batch, args.output, api_token, args.workers)
        sys.exit(0 if results["failed"] == 0 else 1)
    else:
        parser.error("Provide either --prompt (single) or --batch (batch file)")


if __name__ == "__main__":
    main()
