#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

if [ ! -d "node_modules" ]; then
  echo "Installing dependencies..."
  npm install
fi

echo "Rendering IG ENGINE (4K, 47s, 30fps)..."
npx remotion render src/Root.tsx IgEngine \
  .tmp/ig_engine_4k.mp4 \
  --width 3840 --height 2160 \
  --fps 30 --codec h264 --crf 8 \
  --concurrency 4

echo "Done: .tmp/ig_engine_4k.mp4"
echo ""
echo "To add audio, run:"
echo "  bash ../../scripts/merge_audio.sh .tmp/ig_engine_4k.mp4 <path-to-otis.mp3> .tmp/ig_engine_final.mp4 47"
