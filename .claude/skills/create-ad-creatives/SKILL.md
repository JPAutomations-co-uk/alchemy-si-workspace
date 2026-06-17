---
name: create-ad-creatives
description: Generate carousel, single-image, and animated video ad creatives for Instagram. Use when user asks to create ads, generate ad creatives, build carousel ads, make Instagram ads, design ad images, or create video ads with motion graphics.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# Create Ad Creatives

## Goal
Generate pixel-perfect Instagram ad creatives at scale — static PNG images and animated MP4 videos. All templates are fully parametric: brand colors, fonts, logos, and hero images are injected per client. 35 templates total (25 static + 10 animated video).

## Inputs

**Option A: Brand Kit JSON** — Structured JSON with brand colors, fonts, logos, messaging
**Option B: URL Scrape** — Provide a website URL; script extracts colors, images, and context
**Option C: Text Prompt** — Describe the brand and ad requirements in plain text

### Ad Brief Fields
| Field | Required | Description |
|---|---|---|
| brand_name | Yes | Company/brand name |
| target_audience | No | Who the ads target |
| brand_colors.primary | Yes | Main brand color (hex). Secondary and accent auto-generated if missing |
| fonts.heading / fonts.body | No | Google Font names (default: Inter) |
| logo_path | No | Path to logo file (PNG/JPG/SVG/WebP) — embedded base64 into all templates |
| hero_images | No | Array of photo/image paths — used as background in photo templates |
| offers | No | List of offers/promotions for CTAs |
| cta_text | No | Default CTA button text (default: "Learn More") |
| ad_requests | Yes | Array of ads to generate (type, template, topic, dimensions) |

### Instagram Dimensions
- `1080x1080` — Square feed (default)
- `1080x1350` — Portrait 4:5 feed (recommended for Instagram)
- `1080x1920` — Stories/Reels

---

## Static Image Templates (25)

All produce PNG via Playwright screenshot. Specify `"type": "single"` in ad_requests.

### Text-Only (no photo needed)
| Template | Use when |
|---|---|
| `ig_bold_headline` | Brand statement, awareness — big typography, gradient bg |
| `ig_offer_deal` | Price/discount promotion — large number, urgency strip |
| `ig_stats_number` | Social proof via statistics — giant stat + context |
| `ig_pain_point` | Problem-agitate — dark moody, resonates with struggle |
| `ig_bullet_benefits` | Feature/benefit list — 3 checkmark bullets |
| `ig_guarantee` | Trust/authority — circular guarantee badge |
| `ig_free_offer` | Lead gen — "FREE" dominant, low friction |

### Brand-Forward
| Template | Use when |
|---|---|
| `ig_logo_hero` | Brand awareness — large centred logo, tagline |
| `ig_announcement` | Product/service launch — "INTRODUCING" feel |
| `ig_luxury_minimal` | Premium/high-end brands — editorial whitespace |
| `ig_dark_premium` | Luxury with dark aesthetic — gold accents |

### CTA / Conversion
| Template | Use when |
|---|---|
| `ig_strong_cta` | Conversion-focused — CTA block dominates bottom |
| `ig_countdown` | Urgency — limited time, "48 HOURS ONLY" |
| `ig_contact` | Lead gen / booking — split panel with contact feel |

### Photo + Text (requires `hero_images` in brief)
| Template | Use when |
|---|---|
| `ig_photo_overlay` | Hero photo with gradient overlay + copy at bottom |
| `ig_split_h` | Photo top 55%, branded copy bottom |
| `ig_split_v` | Photo left 45%, branded copy right |
| `ig_photo_frame` | Photo inside thick branded border/frame |
| `ig_angled_split` | Diagonal clip-path split — photo + brand |
| `ig_circle_photo` | Circular cropped photo — editorial feel |
| `ig_corner_photo` | Photo fills corner, bold copy opposite |

### Social Proof / Complex
| Template | Use when |
|---|---|
| `ig_testimonial` | Quote + stars + customer attribution |
| `ig_comparison` | Us vs them / without vs with — two columns |
| `ig_results` | Before → After metric showcase |
| `ig_case_study` | Problem → Solution → Result — 3-row layout |

---

## Animated Video Templates (10)

All produce MP4 via `generate_ad_video.py` (Playwright recording → FFmpeg). Specify `"type": "video"` in ad_requests. Default 15s, Instagram-ready.

| Template | Motion concept | Duration |
|---|---|---|
| `igv_gradient_flow` | Morphing gradient background + floating colour orbs + staggered text reveal | 15s |
| `igv_logo_reveal` | Logo builds from animated SVG lines → logo fades in → text stagger reveal | 10s |
| `igv_slide_sequence` | Elements slide in from alternating directions with spring easing | 15s |
| `igv_neon_pulse` | Dark background, neon glow text, pulsing border, scanline sweep | 12s |
| `igv_geometric` | Animated SVG shapes (circles, triangles, lines) build the composition | 15s |
| `igv_typewriter` | Headline types character by character with blinking cursor | 12s |
| `igv_counter` | Number counts up from 0 → target stat with ease-out animation | 10s |
| `igv_split_reveal` | Two panels slide apart to reveal content behind — cinematic reveal | 12s |
| `igv_particle` | Canvas particle field with connected dots — text overlaid | 15s |
| `igv_cinematic` | Letterbox bars animate in, Ken Burns on hero photo, dramatic reveal | 15s |
| `igv_content_engine` | IG ENGINE product ad — 5-scene narrative, beat-synced (94 BPM), glassmorphism + gradient mesh + magnetic snap cubic-bezier. Designed for "Otis" by Kanye/Jay-Z. 9:16 format. | 47s |
| `igv_content_engine_v2` | IG ENGINE V2 — exact JP Automations design system (black bg, teal #2DD4BF, `bg-white/[0.02]` cards, `[+]` mono markers, grid overlay, noise texture, hero blur reveal). 16:9 YouTube format, beat-synced to "Otis" 94 BPM. Use `merge_audio.sh` for final audio merge. | 47s |

---

## Scripts
| Script | Purpose |
|---|---|
| `scripts/parse_ad_brief.py` | Normalize any input (JSON/URL/prompt) into `ad_brief.json` |
| `scripts/research_competitors.py` | Optional competitor ad pattern analysis |
| `scripts/generate_ad_copy.py` | Generate ad copy variations via Claude (parallel workers) |
| `scripts/generate_ad_backgrounds.py` | Generate Flux Pro photorealistic backgrounds for photo templates |
| `scripts/generate_ad_html.py` | Inject copy + brand + backgrounds into HTML templates → HTML files |
| `scripts/screenshot_ads.py` | Playwright: HTML → PNG at exact pixel dimensions |
| `scripts/generate_ad_video.py` | Playwright: animated HTML → WebM → MP4 (FFmpeg) |
| `scripts/compile_ad_package.py` | Package deliverables + optional Meta export |

---

## Process — Static Image Ads

### Step 1: Parse ad brief
```bash
# From JSON:
python3 .claude/skills/create-ad-creatives/scripts/parse_ad_brief.py --json brief.json --output .tmp/ad_brief.json

# From prompt:
python3 .claude/skills/create-ad-creatives/scripts/parse_ad_brief.py \
  --prompt "Landscaping company, green brand, hero photo of garden" --output .tmp/ad_brief.json
```

Review generated `ad_brief.json`. Key fields to check: `brand_colors`, `logo_path`, `hero_images`, `ad_requests`.

### Step 2 (Optional): Research competitors
```bash
python3 .claude/skills/create-ad-creatives/scripts/research_competitors.py \
  --competitors "competitor1.com,competitor2.com" \
  --brief .tmp/ad_brief.json --output .tmp/competitor_research.json
```

### Step 3: Generate ad copy
```bash
python3 .claude/skills/create-ad-creatives/scripts/generate_ad_copy.py \
  --brief .tmp/ad_brief.json --variations 2 --workers 3 --output .tmp/ad_copy.json
```

### Step 3.5: Generate AI backgrounds for photo templates
```bash
python3 .claude/skills/create-ad-creatives/scripts/generate_ad_backgrounds.py \
  --brief .tmp/ad_brief.json --copy .tmp/ad_copy.json --output .tmp/ad_backgrounds/
```
Generates Flux Pro photorealistic backgrounds for photo templates (`ig_photo_overlay`, `ig_split_h`, `ig_split_v`, `ig_photo_frame`, `ig_angled_split`, `ig_circle_photo`, `ig_corner_photo`). Text-only templates are skipped automatically. Requires `REPLICATE_API_TOKEN`. Use `--model black-forest-labs/flux-2-pro` for higher quality.

### Step 4: Generate HTML creatives
```bash
# Without AI backgrounds (text-only templates work fine):
python3 .claude/skills/create-ad-creatives/scripts/generate_ad_html.py \
  --brief .tmp/ad_brief.json --copy .tmp/ad_copy.json --output .tmp/ad_html/

# With AI backgrounds (photo templates get Flux Pro images):
python3 .claude/skills/create-ad-creatives/scripts/generate_ad_html.py \
  --brief .tmp/ad_brief.json --copy .tmp/ad_copy.json \
  --backgrounds .tmp/ad_backgrounds/backgrounds_manifest.json --output .tmp/ad_html/
```

### Step 5: Screenshot to PNG
```bash
python3 .claude/skills/create-ad-creatives/scripts/screenshot_ads.py \
  --input .tmp/ad_html/ --output .tmp/ad_images/ --scale 2
```

### Step 6: Compile package
```bash
python3 .claude/skills/create-ad-creatives/scripts/compile_ad_package.py \
  --images .tmp/ad_images/ --copy .tmp/ad_copy.json \
  --brief .tmp/ad_brief.json --output .tmp/ad_package/
```

---

## Process — Animated Video Ads

### Quick single video (no JSON needed)
```bash
python3 .claude/skills/create-ad-creatives/scripts/generate_ad_video.py \
  --template igv_gradient_flow \
  --headline "We Scale Businesses" \
  --subheadline "Without the agency markup" \
  --cta "Book a Free Call" \
  --brand-name "Acme Agency" \
  --accent "#FF6B35" \
  --logo path/to/logo.png \
  --output .tmp/ads/
```

### From brief + copy (batch)
```bash
# Add video ad_requests to your brief with "type": "video", "template": "igv_neon_pulse"
python3 .claude/skills/create-ad-creatives/scripts/generate_ad_video.py \
  --brief .tmp/ad_brief.json --copy .tmp/ad_copy.json --output .tmp/ad_videos/
```

### Render all video templates (gallery)
```bash
python3 .claude/skills/create-ad-creatives/scripts/generate_ad_video.py \
  --all-templates --headline "Your Headline" --subheadline "Your message" \
  --brand-name "Brand" --output .tmp/video_gallery/
```

### Video options
| Flag | Default | Description |
|---|---|---|
| `--dimensions` | `1080x1080` | `1080x1080`, `1080x1350`, or `1080x1920` |
| `--duration` | template default | Override animation duration in seconds |
| `--hero-image` | — | Path to background photo (for igv_cinematic etc.) |
| `--logo` | — | Path to logo file |

---

## Outputs
- **Static:** `.tmp/ad_package_{brand}/` — PNG files + copy JSON + manifest
- **Video:** `.tmp/ad_videos/` — MP4 files (H.264, yuv420p, Instagram-ready) + `video_manifest.json`

## Environment
- `ANTHROPIC_API_KEY` — Required (copy generation)
- `REPLICATE_API_TOKEN` — Optional (Flux Pro photorealistic backgrounds)
- `playwright install chromium` — One-time setup
- `ffmpeg` — Required for video ads (`brew install ffmpeg`)

## Attaching Client Assets
When a client provides their own assets:
- **Logo:** Set `logo_path` in brief — embedded as base64 into every template automatically
- **Photo/hero image:** Set `hero_images: ["path/to/photo.jpg"]` — used in all `ig_photo_*` templates and `igv_cinematic`
- Accepted formats: PNG, JPG, WebP, SVG (logo only)
- Tip: ask client for logo on transparent PNG background for cleanest result

## Adding New Templates
1. Create `templates/ig_TEMPLATENAME.html` (static) or `templates/igv_TEMPLATENAME.html` (video)
2. Use `{headline}`, `{subheadline}`, `{cta}`, `{logo_html}`, `{hero_image_html}` as placeholders
3. All CSS `{` and `}` must be doubled: `{{` and `}}`
4. For static: register in `SINGLE_BUILDERS` dict in `generate_ad_html.py` using `_make_ig_builder('ig_TEMPLATENAME')`
5. For video: add duration to `TEMPLATE_DURATIONS` dict in `generate_ad_video.py`

## Edge Cases
- **Missing brand colors**: Auto-generates secondary (darker shade) and accent (complementary hue) from primary
- **No logo**: Templates show brand name text fallback
- **No hero image**: Photo templates fall back to brand color gradient
- **Playwright not installed**: Script prints setup instructions
- **FFmpeg not installed**: `brew install ffmpeg` — required for video MP4 output
- **Video recording too short**: Playwright records at realtime — ensure `--duration` covers full animation
- **Rate limiting on copy**: Exponential backoff retry (up to 3 attempts per variation)
