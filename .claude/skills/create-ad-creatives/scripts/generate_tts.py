#!/usr/bin/env python3
"""
Generate voiceover segments using OpenAI TTS-1-HD.

Usage:
    python3 generate_tts.py --output .tmp/mailpulse_tts/
    python3 generate_tts.py --output .tmp/mailpulse_tts/ --voice echo
    python3 generate_tts.py --output .tmp/mailpulse_tts/ --sample  # first segment only
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SEGMENTS = [
    {
        "id": "seg1_hook",
        "scene": "s1",
        "text": "Nearly half of hotel emails go unanswered for over four hours. Every missed email is a missed booking.",
    },
    {
        "id": "seg2_cost",
        "scene": "s2",
        "text": "That's twelve missed enquiries a week, at a hundred and eighty pounds each. Over two thousand pounds walking out the door — with zero visibility into where it's happening.",
    },
    {
        "id": "seg3_dashboard",
        "scene": "s3_dash",
        "text": "MailPulse connects to your team's inboxes and builds a real-time dashboard. Response rates, average reply times, volume — all in one view. You can see exactly where your team stands.",
    },
    {
        "id": "seg4_unanswered",
        "scene": "s3_ua",
        "text": "The unanswered queue shows every email still waiting. Colour-coded badges tell you instantly — green is fine, amber needs attention, red is costing you money.",
    },
    {
        "id": "seg5_logo",
        "scene": "s5_s6",
        "text": "MailPulse. See everything. Miss nothing.",
    },
    {
        "id": "seg6_features",
        "scene": "s7",
        "text": "Every metric across your whole team in one dashboard. Instantly spot who needs support. Catch dropped emails before they cost you bookings. And setup takes seconds — connect Google or Microsoft with one click.",
    },
    {
        "id": "seg7_trust",
        "scene": "s8",
        "text": "And your emails stay private. MailPulse reads metadata only — never the content. Track response times. Spot bottlenecks. Hold your team accountable.",
    },
    {
        "id": "seg8_cta",
        "scene": "s9",
        "text": "MailPulse. Email analytics your team actually needs. Try it free today at jpautomations.co.uk.",
    },
]


def get_duration(filepath):
    """Get audio duration in seconds via ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", filepath],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def generate_segments(output_dir, voice="onyx", model="tts-1-hd", sample_only=False):
    """Generate TTS segments and return manifest."""
    from openai import OpenAI
    client = OpenAI()

    os.makedirs(output_dir, exist_ok=True)
    manifest = []
    segments = SEGMENTS[:1] if sample_only else SEGMENTS

    for seg in segments:
        out_path = os.path.join(output_dir, f"{seg['id']}.mp3")
        print(f"  Generating: {seg['id']}...")

        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=seg["text"],
            response_format="mp3",
        )
        response.stream_to_file(out_path)

        duration = get_duration(out_path)
        manifest.append({
            "id": seg["id"],
            "scene": seg["scene"],
            "file": os.path.abspath(out_path),
            "duration": round(duration, 2),
            "text": seg["text"],
        })
        print(f"    Duration: {duration:.2f}s")

    manifest_path = os.path.join(output_dir, "tts_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    total = sum(s["duration"] for s in manifest)
    print(f"\n  Total voiceover: {total:.1f}s")
    print(f"  Manifest: {manifest_path}")
    return manifest


def stitch_voiceover(manifest, output_path, gap_seconds=0.8):
    """Concatenate TTS segments with silence gaps into one MP3."""
    inputs = []
    filter_parts = []
    idx = 0

    for i, seg in enumerate(manifest):
        inputs.extend(["-i", seg["file"]])
        filter_parts.append(f"[{idx}:a]")
        idx += 1
        if i < len(manifest) - 1:
            inputs.extend(["-f", "lavfi", "-t", str(gap_seconds),
                          "-i", f"anullsrc=r=44100:cl=stereo"])
            filter_parts.append(f"[{idx}:a]")
            idx += 1

    filter_str = "".join(filter_parts) + f"concat=n={len(filter_parts)}:v=0:a=1[out]"

    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", filter_str,
        "-map", "[out]",
        "-c:a", "libmp3lame", "-b:a", "192k",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  Stitch error: {result.stderr[-500:]}", file=sys.stderr)
        return False

    duration = get_duration(output_path)
    print(f"  Stitched voiceover: {output_path} ({duration:.1f}s)")
    return True


def compute_scene_timings(manifest, gap_seconds=0.8):
    """Return dict of scene_id -> start_time_ms and segment durations."""
    timings = {}
    durations = {}
    cursor = 0.0

    for seg in manifest:
        timings[seg["scene"]] = int(cursor * 1000)
        durations[seg["id"]] = seg["duration"]
        cursor += seg["duration"] + gap_seconds

    cursor -= gap_seconds  # no trailing gap
    timings["total_duration"] = round(cursor, 2)
    return timings, durations


def main():
    parser = argparse.ArgumentParser(description="Generate voiceover via OpenAI TTS")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--voice", default="onyx", help="TTS voice (onyx/echo/nova/alloy/fable/shimmer)")
    parser.add_argument("--model", default="tts-1-hd", help="TTS model")
    parser.add_argument("--sample", action="store_true", help="Generate first segment only")
    parser.add_argument("--stitch", action="store_true", help="Also stitch segments into one file")
    args = parser.parse_args()

    print(f"Generating TTS with voice={args.voice}, model={args.model}")
    manifest = generate_segments(args.output, args.voice, args.model, args.sample)

    if args.stitch and not args.sample:
        stitch_path = os.path.join(args.output, "voiceover_stitched.mp3")
        stitch_voiceover(manifest, stitch_path)

        timings, durations = compute_scene_timings(manifest)
        timings_path = os.path.join(args.output, "scene_timings.json")
        with open(timings_path, "w") as f:
            json.dump({"timings": timings, "durations": durations}, f, indent=2)
        print(f"  Scene timings: {timings_path}")
        print(f"  Total duration: {timings['total_duration']:.1f}s")


if __name__ == "__main__":
    main()
