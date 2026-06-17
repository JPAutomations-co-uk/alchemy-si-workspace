import React from "react";
import {
  AbsoluteFill,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
} from "remotion";
import { SCENE_FRAMES, XFADE } from "./utils/beat";
import { COLORS, getFontFaces } from "./utils/theme";
import { GradientMesh } from "./components/GradientMesh";
import { GridOverlay } from "./components/GridOverlay";
import { NoiseTexture } from "./components/NoiseTexture";
import { Scene1Struggle } from "./scenes/Scene1Struggle";
import { Scene2Snap } from "./scenes/Scene2Snap";
import { Scene3Engine } from "./scenes/Scene3Engine";
import { Scene4Dreams } from "./scenes/Scene4Dreams";
import { Scene5CTA } from "./scenes/Scene5CTA";

function computeMeshIntensity(frame: number): number {
  const { scene1End, scene2Start, scene3Start, scene4Start, scene5Start } =
    SCENE_FRAMES;
  return interpolate(
    frame,
    [0, 77, scene2Start - 38, scene2Start, scene3Start, scene4Start, scene5Start, 1410],
    [0.03, 0.1, 0.03, 0.7, 0.5, 0.4, 0.4, 0.35],
    { extrapolateRight: "clamp", extrapolateLeft: "clamp" },
  );
}

function computeMeshWarmth(frame: number): number {
  const { scene1End } = SCENE_FRAMES;
  // Warmth peaks during scatter/stress (bar 6 ~frame 440), then drops
  return interpolate(
    frame,
    [0, 300, 440, scene1End, scene1End + 10],
    [0, 0, 0.3, 0.15, 0],
    { extrapolateRight: "clamp", extrapolateLeft: "clamp" },
  );
}

function computeGridOpacity(frame: number): number {
  const { scene2Start, scene5Start } = SCENE_FRAMES;
  return interpolate(
    frame,
    [0, 60, scene2Start, scene2Start + 10, scene5Start, scene5Start + 10],
    [0, 0.15, 0.15, 0.25, 0.25, 0.12],
    { extrapolateRight: "clamp", extrapolateLeft: "clamp" },
  );
}

export const IgEngine: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const meshIntensity = computeMeshIntensity(frame);
  const meshWarmth = computeMeshWarmth(frame);
  const gridOpacity = computeGridOpacity(frame);

  const s1Duration = SCENE_FRAMES.scene1End + XFADE;
  const s2Duration =
    SCENE_FRAMES.scene2End - SCENE_FRAMES.scene2Start + XFADE * 2;
  const s3Duration =
    SCENE_FRAMES.scene3End - SCENE_FRAMES.scene3Start + XFADE * 2;
  const s4Duration =
    SCENE_FRAMES.scene4End - SCENE_FRAMES.scene4Start + XFADE * 2;
  const s5Duration =
    SCENE_FRAMES.scene5End - SCENE_FRAMES.scene5Start + XFADE;

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.bg }}>
      {/* Inject font faces */}
      <style dangerouslySetInnerHTML={{ __html: getFontFaces() }} />

      {/* Background layers (always present) */}
      <GradientMesh intensity={meshIntensity} warmth={meshWarmth} />
      <GridOverlay opacity={gridOpacity} />
      <NoiseTexture />

      {/* Vignette overlay */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse 75% 65% at 50% 50%, transparent 35%, rgba(0,0,0,0.55) 100%)",
          pointerEvents: "none",
          zIndex: 3,
        }}
      />

      {/* Scene 1: The Struggle (0:00–0:17) */}
      <Sequence
        from={SCENE_FRAMES.scene1Start}
        durationInFrames={s1Duration}
      >
        <Scene1Struggle />
      </Sequence>

      {/* Scene 2: The Snap (0:17–0:22) — BEAT DROP */}
      <Sequence
        from={SCENE_FRAMES.scene2Start - XFADE}
        durationInFrames={s2Duration}
      >
        <Scene2Snap enterDelay={XFADE} />
      </Sequence>

      {/* Scene 3: The Engine (0:22–0:32) */}
      <Sequence
        from={SCENE_FRAMES.scene3Start - XFADE}
        durationInFrames={s3Duration}
      >
        <Scene3Engine enterDelay={XFADE} />
      </Sequence>

      {/* Scene 4: Dream States (0:32–0:42) */}
      <Sequence
        from={SCENE_FRAMES.scene4Start - XFADE}
        durationInFrames={s4Duration}
      >
        <Scene4Dreams enterDelay={XFADE} />
      </Sequence>

      {/* Scene 5: CTA (0:42–0:47) */}
      <Sequence
        from={SCENE_FRAMES.scene5Start - XFADE}
        durationInFrames={s5Duration}
      >
        <Scene5CTA enterDelay={XFADE} />
      </Sequence>
    </AbsoluteFill>
  );
};
