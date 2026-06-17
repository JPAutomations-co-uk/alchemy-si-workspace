#!/usr/bin/env bash
# Merge audio track with silent Playwright video output.
# Usage: ./merge_audio.sh <video.mp4> <audio.mp3> [output.mp4] [duration_seconds]
set -euo pipefail

VIDEO="${1:?Usage: merge_audio.sh <video.mp4> <audio.mp3> [output.mp4] [duration]}"
AUDIO="${2:?Provide audio file as second argument}"
OUTPUT="${3:-${VIDEO%.mp4}_with_audio.mp4}"
DURATION="${4:-47}"

ffmpeg -y \
  -i "$VIDEO" \
  -ss 0 -t "$DURATION" -i "$AUDIO" \
  -c:v copy -c:a aac -b:a 192k \
  -t "$DURATION" -movflags +faststart \
  -shortest \
  "$OUTPUT"

echo "Merged: $OUTPUT"
