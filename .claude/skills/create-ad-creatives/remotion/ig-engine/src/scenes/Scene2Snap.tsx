import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
} from "remotion";
import { beatToFrame, beatPulseScale } from "../utils/beat";
import { magneticSnap, heroReveal } from "../utils/easing";
import { COLORS, FONTS, FONT_WEIGHTS } from "../utils/theme";
import { GlassmorphismCard } from "../components/GlassmorphismCard";

interface Scene2SnapProps {
  enterDelay?: number;
}

// 6 organized grid cells (3x2)
const GRID_LABELS = [
  "Automated Reels",
  "AI Captions",
  "Smart Scheduling",
  "Brand Templates",
  "Content Calendar",
  "Analytics Dashboard",
];

export const Scene2Snap: React.FC<Scene2SnapProps> = ({ enterDelay = 21 }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const S = width / 1920;

  // Scene opacity envelope
  const sceneIn = interpolate(frame, [0, enterDelay], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const totalFrames = beatToFrame(8) + enterDelay * 2; // ~8 beats duration
  const sceneOut = interpolate(
    frame,
    [totalFrames - 21, totalFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
  const sceneOpacity = sceneIn * sceneOut;

  const localFrame = frame - enterDelay;

  // Grid dimensions
  const cols = 3;
  const rows = 2;
  const cellW = 280 * S;
  const cellH = 120 * S;
  const gap = 16 * S;
  const gridW = cols * cellW + (cols - 1) * gap;
  const gridH = rows * cellH + (rows - 1) * gap;
  const gridLeft = (width - gridW) / 2;
  const gridTop = height * 0.28;

  // How many frames per cell stagger
  const cellStagger = 4; // ~120ms
  const cellDuration = 18; // ~600ms

  // Word-by-word starts after cells land
  const wordsStart = Math.round(cellStagger * 5 + cellDuration + 10);

  return (
    <AbsoluteFill style={{ opacity: sceneOpacity, zIndex: 10 }}>
      {/* Grid cells */}
      {GRID_LABELS.map((label, i) => {
        const col = i % cols;
        const row = Math.floor(i / cols);
        const cellStart = Math.max(0, localFrame - i * cellStagger);

        const snapProgress = interpolate(
          cellStart,
          [0, cellDuration],
          [0, 1],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: magneticSnap },
        );

        const cellOpacity = interpolate(
          cellStart,
          [0, cellDuration * 0.6],
          [0, 1],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
        );

        const cellScale = 0.95 + 0.05 * snapProgress;
        const x = gridLeft + col * (cellW + gap);
        const y = gridTop + row * (cellH + gap);

        // Beat pulse after all cells have landed
        const allLanded = localFrame > cellStagger * 5 + cellDuration + 5;
        const pulseScale = allLanded ? beatPulseScale(frame, 0.006) : 1;

        // Glow after landing
        const glowing = localFrame > cellStagger * 5 + cellDuration + 12;

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x,
              top: y,
              width: cellW,
              height: cellH,
              opacity: localFrame > 0 ? cellOpacity : 0,
              transform: `scale(${cellScale * pulseScale})`,
              willChange: "transform, opacity",
            }}
          >
            <GlassmorphismCard
              glowing={glowing}
              padding={`${16 * S}px ${20 * S}px`}
              style={{ width: "100%", height: "100%", display: "flex", alignItems: "center", gap: 12 * S }}
            >
              <span
                style={{
                  fontFamily: FONTS.mono,
                  fontSize: 13 * S,
                  color: COLORS.accent,
                  fontWeight: 500,
                }}
              >
                [+]
              </span>
              <span
                style={{
                  fontFamily: FONTS.body,
                  fontSize: 18 * S,
                  color: COLORS.textPrimary,
                  fontWeight: FONT_WEIGHTS.semibold,
                  letterSpacing: "-0.01em",
                }}
              >
                {label}
              </span>
            </GlassmorphismCard>
          </div>
        );
      })}

      {/* Word-by-word: "What if it created itself?" */}
      <div
        style={{
          position: "absolute",
          top: gridTop + gridH + 80 * S,
          left: 0,
          width: "100%",
          display: "flex",
          justifyContent: "center",
        }}
      >
        <WordByWordInline
          text="What if it created itself?"
          localFrame={localFrame}
          startOffset={wordsStart}
          fontSize={72 * S}
        />
      </div>
    </AbsoluteFill>
  );
};

// Inline word-by-word for this scene (using localFrame directly)
const WordByWordInline: React.FC<{
  text: string;
  localFrame: number;
  startOffset: number;
  fontSize: number;
}> = ({ text, localFrame, startOffset, fontSize }) => {
  const words = text.split(" ");
  const frameBetweenWords = 14; // ~480ms, close to 1 beat
  const wordDuration = 24;

  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        gap: fontSize * 0.35,
        fontFamily: FONTS.heading,
        fontWeight: FONT_WEIGHTS.extrabold,
        fontSize,
        letterSpacing: "-0.025em",
        color: COLORS.textPrimary,
      }}
    >
      {words.map((word, i) => {
        const wordStart = startOffset + i * frameBetweenWords;
        const elapsed = localFrame - wordStart;

        const opacity = interpolate(elapsed, [0, wordDuration * 0.5], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: heroReveal,
        });
        const blur = interpolate(elapsed, [0, wordDuration], [6, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: heroReveal,
        });
        const y = interpolate(elapsed, [0, wordDuration], [10, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: heroReveal,
        });

        return (
          <span
            key={i}
            style={{
              opacity: elapsed > 0 ? opacity : 0,
              filter: `blur(${elapsed > 0 ? blur : 6}px)`,
              transform: `translateY(${elapsed > 0 ? y : 10}px)`,
              display: "inline-block",
            }}
          >
            {word}
          </span>
        );
      })}
    </div>
  );
};
