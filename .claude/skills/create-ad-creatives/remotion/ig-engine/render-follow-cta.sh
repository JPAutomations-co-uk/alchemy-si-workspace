#!/bin/bash
# Render FollowCTA overlay with transparent background
# Output: WebM (VP9 with alpha) for overlay use, plus MP4 preview

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Install deps if needed
if [ ! -d "node_modules" ]; then
  echo "Installing dependencies..."
  npm install
fi

OUT_DIR="$(cd ../../../.. && pwd)/.tmp"
mkdir -p "$OUT_DIR"

# ── Transparent overlay (WebM VP9 with alpha) ──
echo "Rendering transparent overlay (WebM)..."
npx remotion render src/Root.tsx FollowCTA "$OUT_DIR/follow_cta_overlay.webm" \
  --codec vp9 \
  --concurrency 4

# ── MP4 preview (black background, for quick viewing) ──
echo "Rendering MP4 preview..."
npx remotion render src/Root.tsx FollowCTA "$OUT_DIR/follow_cta_preview.mp4" \
  --codec h264 \
  --crf 18 \
  --concurrency 4

echo ""
echo "Done!"
echo "  Transparent overlay: $OUT_DIR/follow_cta_overlay.webm"
echo "  MP4 preview:         $OUT_DIR/follow_cta_preview.mp4"
echo ""
echo "To overlay on a video with FFmpeg:"
echo "  ffmpeg -i your_reel.mp4 -i $OUT_DIR/follow_cta_overlay.webm \\"
echo "    -filter_complex \"[0:v][1:v]overlay=0:0:shortest=1\" \\"
echo "    -c:a copy output.mp4"
