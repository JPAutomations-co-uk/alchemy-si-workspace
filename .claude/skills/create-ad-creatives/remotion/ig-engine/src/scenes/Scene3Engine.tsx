import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
} from "remotion";
import { BEAT_DURATION_FRAMES, beatPulseScale } from "../utils/beat";
import { heroReveal, luxEase } from "../utils/easing";
import { COLORS, FONTS, FONT_WEIGHTS, RADII } from "../utils/theme";
import { GlassmorphismCard } from "../components/GlassmorphismCard";
import { Typewriter } from "../components/Typewriter";

interface Scene3EngineProps {
  enterDelay?: number;
}

const FEATURES = [
  { name: "Create Reels", icon: "\u25B6", tokens: "15 tokens" },
  { name: "Create Ads", icon: "\u25CE", tokens: "10 tokens" },
  { name: "Create Carousels", icon: "\u229E", tokens: "10 tokens" },
  { name: "Reel Scripts", icon: "\u270E", tokens: "5 tokens" },
  { name: "Reel Editing", icon: "\u25C8", tokens: "8 tokens" },
  { name: "Caption Writing", icon: "\u2726", tokens: "1 token" },
  { name: "Content Planning", icon: "\u25FB", tokens: "25 tokens" },
];

export const Scene3Engine: React.FC<Scene3EngineProps> = ({
  enterDelay = 21,
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const S = width / 1920;

  // Scene opacity envelope
  const sceneIn = interpolate(frame, [0, enterDelay], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const totalDuration = Math.round(BEAT_DURATION_FRAMES * 15) + enterDelay * 2;
  const sceneOut = interpolate(
    frame,
    [totalDuration - 21, totalDuration],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  const localFrame = frame - enterDelay;

  // App card appears at beat 2 (~38 frames)
  const appCardStart = 38;
  const appCardDuration = 36;
  const appCardProgress = interpolate(
    localFrame,
    [appCardStart, appCardStart + appCardDuration],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: luxEase },
  );
  const appCardOpacity = interpolate(
    localFrame,
    [appCardStart, appCardStart + appCardDuration * 0.5],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
  const appCardScale = 0.97 + 0.03 * appCardProgress;
  const appCardBlur = interpolate(
    localFrame,
    [appCardStart, appCardStart + appCardDuration],
    [8, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: luxEase },
  );

  // Typewriter starts at beat 3 (~57 frames)
  const typewriterStart = 57;

  // Feature cards: 1 per beat starting at beat 4 (~76 frames)
  const featureStart = 76;
  const featureBeatGap = Math.round(BEAT_DURATION_FRAMES); // ~19 frames

  // All cards landed after feature card 7
  const allLandedFrame = featureStart + FEATURES.length * featureBeatGap + 9;

  // Layout
  const appCardW = 400 * S;
  const appCardH = 360 * S;
  const appCardX = width * 0.22;
  const appCardY = height * 0.5 - appCardH / 2;

  const featureCardW = 260 * S;
  const featureCardH = 72 * S;
  const featureGap = 12 * S;
  const featureGridX = width * 0.52;
  const featureGridTop = height * 0.2;
  const featureCols = 2;

  return (
    <AbsoluteFill style={{ opacity: sceneIn * sceneOut, zIndex: 10 }}>
      {/* Central app card */}
      <div
        style={{
          position: "absolute",
          left: appCardX,
          top: appCardY,
          width: appCardW,
          opacity: localFrame >= appCardStart ? appCardOpacity : 0,
          transform: `scale(${appCardScale})`,
          filter: `blur(${appCardBlur}px)`,
          willChange: "transform, opacity, filter",
        }}
      >
        <GlassmorphismCard
          borderRadius={RADII.cardLg}
          padding={`${40 * S}px ${36 * S}px`}
          glowing={localFrame > allLandedFrame}
          style={{ height: appCardH }}
        >
          {/* Eyebrow */}
          <div
            style={{
              fontFamily: FONTS.mono,
              fontSize: 11 * S,
              fontWeight: FONT_WEIGHTS.medium,
              color: COLORS.accent,
              textTransform: "uppercase",
              letterSpacing: "0.25em",
              marginBottom: 20 * S,
            }}
          >
            CONTENT ENGINE
          </div>

          {/* Typewriter title */}
          <Typewriter
            text="IG ENGINE"
            startFrame={localFrame >= 0 ? typewriterStart : 9999}
            charsPerFrame={0.5}
            fontSize={56 * S}
          />

          {/* Subtitle */}
          {(() => {
            const subStart = typewriterStart + 40; // after typewriter finishes
            const subOpacity = interpolate(
              localFrame,
              [subStart, subStart + 20],
              [0, 1],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
            );
            return (
              <div
                style={{
                  fontFamily: FONTS.body,
                  fontSize: 16 * S,
                  color: COLORS.textMuted,
                  marginTop: 16 * S,
                  opacity: localFrame >= subStart ? subOpacity : 0,
                  letterSpacing: "-0.01em",
                }}
              >
                by JPAutomations
              </div>
            );
          })()}
        </GlassmorphismCard>
      </div>

      {/* Feature cards grid */}
      {FEATURES.map((feature, i) => {
        const cardStart = featureStart + i * featureBeatGap;
        const elapsed = localFrame - cardStart;

        const cardProgress = interpolate(elapsed, [0, 24], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: heroReveal,
        });
        const cardOpacity = interpolate(elapsed, [0, 12], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
        const cardScale = 0.97 + 0.03 * cardProgress;
        const cardBlur = interpolate(elapsed, [0, 24], [4, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: heroReveal,
        });

        // Beat pulse after all landed
        const pulse =
          localFrame > allLandedFrame ? beatPulseScale(frame, 0.006) : 1;

        const col = i % featureCols;
        const row = Math.floor(i / featureCols);
        const x = featureGridX + col * (featureCardW + featureGap);
        const y = featureGridTop + row * (featureCardH + featureGap);

        // Physics: push outward when center glows
        const physicsFrame = localFrame - allLandedFrame;
        const physicsOffset =
          physicsFrame > 0 && physicsFrame < 30
            ? interpolate(physicsFrame, [0, 8, 30], [0, 4, 0], {
                extrapolateRight: "clamp",
              }) * (col === 0 ? -1 : 1)
            : 0;

        const glowing = elapsed > 24 + 12;

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x + physicsOffset * S,
              top: y,
              width: featureCardW,
              height: featureCardH,
              opacity: elapsed > 0 ? cardOpacity : 0,
              transform: `scale(${cardScale * pulse})`,
              filter: `blur(${elapsed > 0 ? cardBlur : 4}px)`,
              willChange: "transform, opacity, filter",
            }}
          >
            <GlassmorphismCard
              glowing={glowing}
              padding={`${14 * S}px ${18 * S}px`}
              style={{
                width: "100%",
                height: "100%",
                display: "flex",
                alignItems: "center",
                gap: 12 * S,
              }}
            >
              <span
                style={{
                  fontFamily: FONTS.mono,
                  fontSize: 20 * S,
                  color: COLORS.accent,
                }}
              >
                {feature.icon}
              </span>
              <div style={{ flex: 1 }}>
                <div
                  style={{
                    fontFamily: FONTS.body,
                    fontSize: 16 * S,
                    fontWeight: FONT_WEIGHTS.semibold,
                    color: COLORS.textPrimary,
                    letterSpacing: "-0.01em",
                  }}
                >
                  {feature.name}
                </div>
                <div
                  style={{
                    fontFamily: FONTS.mono,
                    fontSize: 11 * S,
                    color: COLORS.textMuted,
                    marginTop: 2 * S,
                  }}
                >
                  {feature.tokens}
                </div>
              </div>
            </GlassmorphismCard>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
