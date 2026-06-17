#!/usr/bin/env python3
"""
Generate MailPulse walkthrough video with AI voiceover.

End-to-end pipeline:
  1. Generate TTS voiceover segments (OpenAI tts-1-hd)
  2. Stitch into single voiceover track with gaps
  3. Compute scene timings from voiceover durations
  4. Rewrite HTML template setTimeout values
  5. Record 4K video via Playwright
  6. Mix video + voiceover + background music → final MP4

Usage:
    python3 generate_walkthrough_video.py --output .tmp/mailpulse_walkthrough/
    python3 generate_walkthrough_video.py --output .tmp/mailpulse_walkthrough/ --music bg_track.mp3
    python3 generate_walkthrough_video.py --output .tmp/mailpulse_walkthrough/ --skip-tts  # reuse existing TTS
"""

import os
import sys
import json
import argparse
import subprocess
import shutil
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(SCRIPTS_DIR, '..', 'templates')

# Import from sibling scripts
sys.path.insert(0, SCRIPTS_DIR)
from generate_tts import generate_segments, stitch_voiceover, compute_scene_timings, get_duration
from generate_ad_video import record_html_to_webm, convert_webm_to_mp4


def rewrite_template_timings(template_html, timings, durations):
    """Replace hardcoded setTimeout values with voiceover-driven timings."""
    # Split at <script> to avoid touching CSS values
    script_idx = template_html.index("<script>")
    css_part = template_html[:script_idx]
    js_part = template_html[script_idx:]

    # Map old hardcoded values → new voiceover-driven values
    # The feature walkthrough (seg6) is split into 4 equal sub-scenes
    seg6_dur = durations.get("seg6_features", 13.0) * 1000
    feat_start = timings.get("s7", 36000)

    replacements = {
        "}, 5000);":  f"}}, {timings['s2']});",
        "}, 10000);": f"}}, {timings['s3_dash']});",
        "}, 24000);": f"}}, {timings['s5_s6'] - 1000});",  # blackout 1s before logo
        "}, 25000);": f"}}, {timings['s5_s6']});",
        "}, 28000);": f"}}, {feat_start});",
        "}, 32000);": f"}}, {feat_start + int(seg6_dur * 0.25)});",
        "}, 36000);": f"}}, {feat_start + int(seg6_dur * 0.50)});",
        "}, 40000);": f"}}, {feat_start + int(seg6_dur * 0.75)});",
        "}, 44000);": f"}}, {timings['s8']});",
        "}, 52000);": f"}}, {timings['s9']});",
    }

    for old_val, new_val in replacements.items():
        js_part = js_part.replace(old_val, new_val)

    return css_part + js_part


def render_template_with_timings(timings, durations, width=1920, height=1080):
    """Load igv_mailpulse.html, inject dimensions and rewrite timings."""
    template_path = os.path.join(TEMPLATES_DIR, "igv_mailpulse.html")
    with open(template_path, "r") as f:
        html = f.read()

    # Inject width/height (Python .format() — template uses {{ }} for literal braces)
    html = html.format(width=width, height=height)

    # Rewrite scene timings
    html = rewrite_template_timings(html, timings, durations)

    return html


def mix_audio(video_path, voiceover_path, music_path, output_path, duration):
    """Mix video + voiceover + optional background music."""
    if music_path and os.path.exists(music_path):
        # Full mix: voiceover at full volume + music at 12%
        fade_out_start = max(0, duration - 3)
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", voiceover_path,
            "-i", music_path,
            "-filter_complex",
            f"[1:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[vo];"
            f"[2:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,"
            f"volume=0.12,afade=t=in:st=0:d=2,afade=t=out:st={fade_out_start}:d=3[bg];"
            f"[vo][bg]amix=inputs=2:duration=first:dropout_transition=3[mixed]",
            "-map", "0:v", "-map", "[mixed]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            "-t", str(int(duration)),
            output_path
        ]
    else:
        # Voiceover only (no background music)
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", voiceover_path,
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            "-t", str(int(duration)),
            "-shortest",
            output_path
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  Mix error: {result.stderr[-500:]}", file=sys.stderr)
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate MailPulse walkthrough with voiceover")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--music", default=None, help="Background music MP3 (optional)")
    parser.add_argument("--voice", default="onyx", help="TTS voice")
    parser.add_argument("--skip-tts", action="store_true", help="Reuse existing TTS from output dir")
    parser.add_argument("--dimensions", default="3840x2160", help="Video dimensions (default 4K)")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    tts_dir = os.path.join(args.output, "tts")

    # ── Step 1: Generate TTS ──
    if args.skip_tts:
        manifest_path = os.path.join(tts_dir, "tts_manifest.json")
        if not os.path.exists(manifest_path):
            print("Error: --skip-tts but no tts_manifest.json found", file=sys.stderr)
            sys.exit(1)
        with open(manifest_path) as f:
            manifest = json.load(f)
        print(f"  Reusing existing TTS ({len(manifest)} segments)")
    else:
        print("Step 1: Generating voiceover segments...")
        manifest = generate_segments(tts_dir, voice=args.voice)

    # ── Step 2: Stitch voiceover ──
    voiceover_path = os.path.join(args.output, "voiceover.mp3")
    if not args.skip_tts or not os.path.exists(voiceover_path):
        print("\nStep 2: Stitching voiceover...")
        ok = stitch_voiceover(manifest, voiceover_path)
        if not ok:
            sys.exit(1)
    else:
        print(f"  Reusing stitched voiceover: {voiceover_path}")

    # ── Step 3: Compute timings ──
    print("\nStep 3: Computing scene timings...")
    timings, durations = compute_scene_timings(manifest)
    total_duration = timings["total_duration"] + 2  # 2s buffer for final CTA

    timings_path = os.path.join(args.output, "scene_timings.json")
    with open(timings_path, "w") as f:
        json.dump({"timings": timings, "durations": durations, "total": total_duration}, f, indent=2)

    print(f"  Scene timings saved: {timings_path}")
    for scene, ms in sorted(timings.items()):
        if scene != "total_duration":
            print(f"    {scene}: {ms}ms ({ms/1000:.1f}s)")
    print(f"  Total duration: {total_duration:.1f}s")

    # ── Step 4: Rewrite template ──
    print("\nStep 4: Rewriting template timings...")
    dims = args.dimensions.split("x")
    out_w, out_h = int(dims[0]), int(dims[1])
    # For 4K: template uses half viewport
    tmpl_w = out_w // 2 if out_w >= 3840 else out_w
    tmpl_h = out_h // 2 if out_w >= 3840 else out_h

    html = render_template_with_timings(timings, durations, tmpl_w, tmpl_h)
    tmp_html = os.path.join(args.output, "_tmp_walkthrough.html")
    with open(tmp_html, "w") as f:
        f.write(html)
    print(f"  Template written: {tmp_html}")

    # ── Step 5: Record video ──
    print(f"\nStep 5: Recording {out_w}x{out_h} video ({total_duration:.0f}s)...")
    webm_path = os.path.join(args.output, "walkthrough.webm")
    mp4_silent = os.path.join(args.output, "walkthrough_silent.mp4")

    ok = record_html_to_webm(tmp_html, webm_path, out_w, out_h, total_duration)
    if not ok:
        print("  Error: Playwright recording failed", file=sys.stderr)
        sys.exit(1)

    print("  Converting to MP4...")
    ok = convert_webm_to_mp4(webm_path, mp4_silent)
    if not ok:
        print("  Error: FFmpeg conversion failed", file=sys.stderr)
        sys.exit(1)

    # ── Step 6: Mix audio ──
    final_path = os.path.join(args.output, "mailpulse_walkthrough_4k.mp4")
    print(f"\nStep 6: Mixing audio...")
    if args.music:
        print(f"  Voiceover: {voiceover_path}")
        print(f"  Background: {args.music}")
    else:
        print(f"  Voiceover only (no background music)")

    ok = mix_audio(mp4_silent, voiceover_path, args.music, final_path, total_duration)
    if not ok:
        print("  Error: Audio mixing failed", file=sys.stderr)
        sys.exit(1)

    # ── Cleanup ──
    for tmp in [webm_path, tmp_html]:
        if os.path.exists(tmp):
            os.unlink(tmp)

    size_mb = os.path.getsize(final_path) / (1024 * 1024)
    print(f"\n✓ Done: {final_path} ({size_mb:.1f}MB, {total_duration:.0f}s)")
    print(f"  Resolution: {out_w}x{out_h}")
    if not args.music:
        print(f"\n  Tip: Add background music with --music <file.mp3>")


if __name__ == "__main__":
    main()
