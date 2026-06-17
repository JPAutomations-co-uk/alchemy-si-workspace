import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
} from "remotion";
import { BEAT_DURATION_FRAMES } from "../utils/beat";
import { luxEase, heroReveal } from "../utils/easing";
import { COLORS, FONTS, FONT_WEIGHTS, RADII } from "../utils/theme";

interface Scene5CTAProps {
  enterDelay?: number;
}

export const Scene5CTA: React.FC<Scene5CTAProps> = ({ enterDelay = 21 }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const S = width / 1920;

  const localFrame = frame - enterDelay;

  // Scene fade in
  const sceneIn = interpolate(frame, [0, enterDelay], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Beat markers (in local frames)
  const beat1 = Math.round(BEAT_DURATION_FRAMES); // ~19
  const beat3 = Math.round(BEAT_DURATION_FRAMES * 3); // ~57
  const beat4 = Math.round(BEAT_DURATION_FRAMES * 3.5); // ~67
  const beat5 = Math.round(BEAT_DURATION_FRAMES * 4); // ~77
  const beat5b = Math.round(BEAT_DURATION_FRAMES * 5); // ~96
  const beat6 = Math.round(BEAT_DURATION_FRAMES * 6); // ~115

  // Eyebrow: CONTENT ENGINE
  const eyebrowOpacity = interpolate(localFrame, [beat1, beat1 + 18], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Brand name: IG ENGINE (gradient text)
  const brandProgress = interpolate(
    localFrame,
    [beat3, beat3 + 36],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: luxEase },
  );
  const brandOpacity = interpolate(localFrame, [beat3, beat3 + 18], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const brandScale = 0.97 + 0.03 * brandProgress;
  const brandBlur = interpolate(localFrame, [beat3, beat3 + 36], [8, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: luxEase,
  });

  // Headline: "Start generating."
  const headlineProgress = interpolate(
    localFrame,
    [beat4, beat4 + 26],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: heroReveal },
  );
  const headlineOpacity = interpolate(
    localFrame,
    [beat4, beat4 + 15],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
  const headlineScale = 0.97 + 0.03 * headlineProgress;

  // CTA pill button with micro-overshoot
  const ctaElapsed = localFrame - beat5;
  const ctaScale =
    ctaElapsed > 0
      ? interpolate(
          ctaElapsed,
          [0, 12, 18, 24],
          [0.95, 0.99, 1.02, 1.0],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
        )
      : 0.95;
  const ctaOpacity = interpolate(localFrame, [beat5, beat5 + 9], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Teal glow radiates
  const glowElapsed = localFrame - beat5b;
  const glowSpread =
    glowElapsed > 0
      ? interpolate(glowElapsed, [0, 54], [0, 60 * S], {
          extrapolateRight: "clamp",
        })
      : 0;
  const glowOpacity =
    glowElapsed > 0
      ? interpolate(glowElapsed, [0, 30, 54], [0.5, 0.3, 0], {
          extrapolateRight: "clamp",
        })
      : 0;

  // URL
  const urlOpacity = interpolate(localFrame, [beat6, beat6 + 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ opacity: sceneIn, zIndex: 10 }}>
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 20 * S,
        }}
      >
        {/* Eyebrow */}
        <div
          style={{
            fontFamily: FONTS.mono,
            fontSize: 12 * S,
            fontWeight: FONT_WEIGHTS.medium,
            color: COLORS.accent,
            textTransform: "uppercase",
            letterSpacing: "0.25em",
            opacity: localFrame >= beat1 ? eyebrowOpacity : 0,
          }}
        >
          CONTENT ENGINE
        </div>

        {/* Brand name: IG ENGINE */}
        <div
          style={{
            fontFamily: FONTS.mono,
            fontSize: 96 * S,
            fontWeight: FONT_WEIGHTS.extrabold,
            letterSpacing: "-0.02em",
            background: `linear-gradient(to right, ${COLORS.accent}, ${COLORS.accentLight})`,
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
            opacity: localFrame >= beat3 ? brandOpacity : 0,
            transform: `scale(${localFrame >= beat3 ? brandScale : 0.97})`,
            filter: `blur(${localFrame >= beat3 ? brandBlur : 8}px)`,
          }}
        >
          IG ENGINE
        </div>

        {/* Headline */}
        <div
          style={{
            fontFamily: FONTS.heading,
            fontSize: 52 * S,
            fontWeight: FONT_WEIGHTS.extrabold,
            color: COLORS.textPrimary,
            letterSpacing: "-0.025em",
            opacity: localFrame >= beat4 ? headlineOpacity : 0,
            transform: `scale(${localFrame >= beat4 ? headlineScale : 0.97})`,
            marginTop: 8 * S,
          }}
        >
          Start generating.
        </div>

        {/* Subtitle */}
        <div
          style={{
            fontFamily: FONTS.body,
            fontSize: 18 * S,
            color: COLORS.textMuted,
            opacity: localFrame >= beat4 + 9 ? interpolate(localFrame, [beat4 + 9, beat4 + 24], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) : 0,
            marginTop: 4 * S,
          }}
        >
          Instagram content. Generated in seconds.
        </div>

        {/* CTA pill button */}
        <div
          style={{
            position: "relative",
            marginTop: 24 * S,
            opacity: localFrame >= beat5 ? ctaOpacity : 0,
            transform: `scale(${localFrame >= beat5 ? ctaScale : 0.95})`,
          }}
        >
          {/* Glow behind button */}
          <div
            style={{
              position: "absolute",
              inset: -glowSpread,
              borderRadius: RADII.pill,
              boxShadow: `0 0 ${glowSpread}px ${glowSpread * 0.5}px rgba(45,212,191,${glowOpacity})`,
              pointerEvents: "none",
            }}
          />
          <div
            style={{
              padding: `${18 * S}px ${48 * S}px`,
              background: COLORS.accent,
              borderRadius: RADII.pill,
              fontFamily: FONTS.body,
              fontSize: 18 * S,
              fontWeight: FONT_WEIGHTS.semibold,
              color: "#000000",
              letterSpacing: "-0.01em",
            }}
          >
            Get Started
          </div>
        </div>

        {/* URL */}
        <div
          style={{
            fontFamily: FONTS.mono,
            fontSize: 14 * S,
            color: COLORS.textDim,
            letterSpacing: "0.05em",
            opacity: localFrame >= beat6 ? urlOpacity : 0,
            marginTop: 28 * S,
          }}
        >
          jpautomations.co.uk
        </div>
      </div>
    </AbsoluteFill>
  );
};
