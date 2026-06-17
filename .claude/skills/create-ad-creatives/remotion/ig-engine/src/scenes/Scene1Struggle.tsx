import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
} from "remotion";
import { beatToFrame, barToFrame } from "../utils/beat";
import { heroReveal, sharpOut } from "../utils/easing";
import { COLORS, FONTS, FONT_WEIGHTS } from "../utils/theme";
import { ContentIcon } from "../components/ContentIcon";

// Task cards with their rest positions (% of viewport)
const TASK_CARDS = [
  { label: "Write Caption", restX: 0.12, restY: 0.18, scatterAngle: -140 },
  { label: "Film Reel", restX: 0.62, restY: 0.12, scatterAngle: -40 },
  { label: "Design Carousel", restX: 0.08, restY: 0.44, scatterAngle: -170 },
  { label: "Schedule Post", restX: 0.72, restY: 0.38, scatterAngle: 20 },
  { label: "Research Hashtags", restX: 0.15, restY: 0.72, scatterAngle: 200 },
  { label: "Edit Photos", restX: 0.68, restY: 0.65, scatterAngle: 60 },
  { label: "Plan Content", restX: 0.38, restY: 0.28, scatterAngle: -90 },
  { label: "Analyze Metrics", restX: 0.45, restY: 0.78, scatterAngle: 140 },
];

// Entry stagger: cards appear over bars 2-5
const CARD_ENTRY_START = barToFrame(1); // ~bar 2 = frame 77
const CARD_ENTRY_STAGGER = 19; // ~1 beat between cards

// Heading appears at bar 4
const HEADING_START = barToFrame(3); // frame ~230

// Scatter starts at bar 6 beat 4
const SCATTER_START = beatToFrame(23); // frame ~440

// Stillness: everything fades, last ~1.5 bars
const STILLNESS_START = beatToFrame(25); // frame ~479

export const Scene1Struggle: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const S = width / 1920; // scale factor

  // Scene-level fade out at the end
  const sceneOpacity = interpolate(
    frame,
    [beatToFrame(26), beatToFrame(27)],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <AbsoluteFill style={{ opacity: sceneOpacity, zIndex: 10 }}>
      {/* Task cards */}
      {TASK_CARDS.map((card, i) => {
        const entryStart = CARD_ENTRY_START + i * CARD_ENTRY_STAGGER;
        const entryDuration = 45; // ~1.5s fade in

        // Entry opacity
        const entryOpacity = interpolate(
          frame,
          [entryStart, entryStart + entryDuration],
          [0, 1],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
        );

        // Slow sinusoidal drift
        const driftX =
          Math.sin(frame * 0.018 + i * 2.3) * 18 * S;
        const driftY =
          Math.cos(frame * 0.014 + i * 1.7) * 14 * S;

        // Scatter animation
        const scatterProgress = interpolate(
          frame,
          [SCATTER_START, SCATTER_START + 21],
          [0, 1],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: sharpOut },
        );

        const scatterAngleRad = (card.scatterAngle * Math.PI) / 180;
        const scatterDist = 1200 * S * scatterProgress;
        const scatterX = Math.cos(scatterAngleRad) * scatterDist;
        const scatterY = Math.sin(scatterAngleRad) * scatterDist;
        const scatterRotation = (card.scatterAngle * 0.3) * scatterProgress;
        const scatterScale = 1 - 0.4 * scatterProgress;

        // Scatter opacity (fade out faster than movement)
        const scatterOpacity = interpolate(
          frame,
          [SCATTER_START, SCATTER_START + 15],
          [1, 0],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
        );

        const finalOpacity = entryOpacity * scatterOpacity;
        const baseX = card.restX * width;
        const baseY = card.restY * height;

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: baseX + driftX + scatterX,
              top: baseY + driftY + scatterY,
              opacity: finalOpacity,
              transform: `scale(${scatterScale}) rotate(${scatterRotation}deg)`,
              willChange: "transform, opacity",
            }}
          >
            <ContentIcon
              label={card.label}
              fontSize={14 * S}
            />
          </div>
        );
      })}

      {/* Heading: "Creating content shouldn't feel like this." */}
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          textAlign: "center",
          width: "80%",
        }}
      >
        {(() => {
          const headingOpacity = interpolate(
            frame,
            [HEADING_START, HEADING_START + 26],
            [0, 1],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: heroReveal },
          );
          const headingBlur = interpolate(
            frame,
            [HEADING_START, HEADING_START + 26],
            [12, 0],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: heroReveal },
          );
          const headingY = interpolate(
            frame,
            [HEADING_START, HEADING_START + 26],
            [20 * S, 0],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: heroReveal },
          );
          // Fade out with scatter
          const headingFadeOut = interpolate(
            frame,
            [SCATTER_START - 10, SCATTER_START + 5],
            [1, 0],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
          );

          return (
            <div
              style={{
                opacity: headingOpacity * headingFadeOut,
                filter: `blur(${headingBlur}px)`,
                transform: `translateY(${headingY}px)`,
                fontFamily: FONTS.heading,
                fontWeight: FONT_WEIGHTS.extrabold,
                fontSize: 64 * S,
                letterSpacing: "-0.025em",
                lineHeight: 1.1,
                color: COLORS.textPrimary,
              }}
            >
              Creating content shouldn't
              <br />
              feel like this.
            </div>
          );
        })()}
      </div>
    </AbsoluteFill>
  );
};
