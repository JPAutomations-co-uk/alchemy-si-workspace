export const BPM = 94;
export const FPS = 30;
export const BEAT_DURATION_SECONDS = 60 / BPM; // 0.6383s
export const BEAT_DURATION_FRAMES = FPS * BEAT_DURATION_SECONDS; // 19.1489

/** Convert beat number to frame number */
export function beatToFrame(beat: number): number {
  return Math.round(beat * BEAT_DURATION_FRAMES);
}

/** Convert frame to the current beat (fractional) */
export function frameToBeat(frame: number): number {
  return frame / BEAT_DURATION_FRAMES;
}

/** Get the frame of the Nth bar (4 beats per bar) */
export function barToFrame(bar: number): number {
  return beatToFrame(bar * 4);
}

/** Returns 0-1 progress within the current beat */
export function beatPhase(frame: number): number {
  const beat = frameToBeat(frame);
  return beat - Math.floor(beat);
}

/**
 * Returns a scale multiplier that pulses on each beat.
 * Sharp attack, soft decay — syncs with the music's rhythm.
 */
export function beatPulseScale(
  frame: number,
  amplitude: number = 0.006,
): number {
  const phase = beatPhase(frame);
  const pulse =
    phase < 0.15
      ? Math.sin((phase / 0.15) * Math.PI * 0.5) // quick rise
      : Math.cos(((phase - 0.15) / 0.85) * Math.PI * 0.5); // slow fall
  return 1 + pulse * amplitude;
}

/** Scene boundaries in frames */
export const SCENE_FRAMES = {
  scene1Start: 0,
  scene1End: beatToFrame(27), // ~517, 17.2s
  scene2Start: beatToFrame(27),
  scene2End: beatToFrame(35), // ~670, 22.3s
  scene3Start: beatToFrame(35),
  scene3End: beatToFrame(50), // ~957, 31.9s
  scene4Start: beatToFrame(50),
  scene4End: beatToFrame(65), // ~1245, 41.5s
  scene5Start: beatToFrame(65),
  scene5End: 1410, // 47s
} as const;

/** Crossfade overlap in frames (~700ms) */
export const XFADE = 21;
