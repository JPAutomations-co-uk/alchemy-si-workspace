import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Easing,
} from "remotion";
import { magneticSnap, heroReveal, luxEase } from "../utils/easing";
import { COLORS, FONTS, FONT_WEIGHTS } from "../utils/theme";
import { ProgressBar } from "../components/ProgressBar";
import { PhoneMockup } from "../components/PhoneMockup";

interface Scene4DreamsProps {
  enterDelay?: number;
}

export const Scene4Dreams: React.FC<Scene4DreamsProps> = ({
  enterDelay = 21,
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const S = width / 1920;

  const localFrame = frame - enterDelay;

  // Scene envelope
  const sceneIn = interpolate(frame, [0, enterDelay], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // 3 vignettes, each ~105 frames (3.5s), with 9-frame crossfade overlap
  const vigA = { start: 0, end: 105 };
  const vigB = { start: 96, end: 201 };
  const vigC = { start: 192, end: 297 };

  // Vignette A opacity
  const vigAOpacity =
    localFrame >= vigA.start && localFrame <= vigA.end
      ? interpolate(localFrame, [vigA.start, vigA.start + 12, vigA.end - 12, vigA.end], [0, 1, 1, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        })
      : 0;

  // Vignette B opacity
  const vigBOpacity =
    localFrame >= vigB.start && localFrame <= vigB.end
      ? interpolate(localFrame, [vigB.start, vigB.start + 12, vigB.end - 12, vigB.end], [0, 1, 1, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        })
      : 0;

  // Vignette C opacity
  const vigCOpacity =
    localFrame >= vigC.start && localFrame <= vigC.end
      ? interpolate(localFrame, [vigC.start, vigC.start + 12, vigC.end - 12, vigC.end], [0, 1, 1, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        })
      : 0;

  return (
    <AbsoluteFill style={{ opacity: sceneIn, zIndex: 10 }}>
      {/* Vignette A: "A month of content. Minutes to make." */}
      <AbsoluteFill style={{ opacity: vigAOpacity }}>
        <VignetteA localFrame={localFrame - vigA.start} S={S} width={width} height={height} />
      </AbsoluteFill>

      {/* Vignette B: "Every reel. Every carousel. On brand." */}
      <AbsoluteFill style={{ opacity: vigBOpacity }}>
        <VignetteB localFrame={localFrame - vigB.start} S={S} width={width} height={height} />
      </AbsoluteFill>

      {/* Vignette C: "You describe it. We generate it." */}
      <AbsoluteFill style={{ opacity: vigCOpacity }}>
        <VignetteC localFrame={localFrame - vigC.start} S={S} width={width} height={height} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---- Vignette A: Counter + Calendar ----
const VignetteA: React.FC<{ localFrame: number; S: number; width: number; height: number }> = ({
  localFrame,
  S,
  width,
  height,
}) => {
  // Counter 0→30 over 66 frames (2.2s)
  const counterValue = Math.round(
    interpolate(localFrame, [0, 66], [0, 30], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.out(Easing.cubic),
    }),
  );

  // Calendar grid: 7 cols x 4 rows = 28 cells
  const cellCount = 28;
  const cellsVisible = Math.min(
    cellCount,
    Math.max(0, Math.floor((localFrame - 5) / 1.5)),
  );

  // Text appears at frame 66
  const textOpacity = interpolate(localFrame, [66, 90], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: heroReveal,
  });
  const textBlur = interpolate(localFrame, [66, 90], [8, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: heroReveal,
  });

  const cellSize = 36 * S;
  const cellGap = 6 * S;
  const gridCols = 7;

  return (
    <>
      {/* Giant counter */}
      <div
        style={{
          position: "absolute",
          top: height * 0.2,
          left: 0,
          width: "100%",
          textAlign: "center",
          fontFamily: FONTS.mono,
          fontSize: 180 * S,
          fontWeight: FONT_WEIGHTS.extrabold,
          color: COLORS.accent,
          letterSpacing: "-0.04em",
          lineHeight: 1,
        }}
      >
        {counterValue}
      </div>

      {/* Calendar grid */}
      <div
        style={{
          position: "absolute",
          top: height * 0.52,
          left: "50%",
          transform: "translateX(-50%)",
          display: "grid",
          gridTemplateColumns: `repeat(${gridCols}, ${cellSize}px)`,
          gap: cellGap,
        }}
      >
        {Array.from({ length: cellCount }).map((_, i) => (
          <div
            key={i}
            style={{
              width: cellSize,
              height: cellSize,
              borderRadius: 6 * S,
              background: i < cellsVisible ? COLORS.accent : "rgba(255,255,255,0.03)",
              opacity: i < cellsVisible ? 0.8 : 0.3,
              border: `1px solid ${i < cellsVisible ? "rgba(45,212,191,0.3)" : "rgba(255,255,255,0.06)"}`,
            }}
          />
        ))}
      </div>

      {/* Text */}
      <div
        style={{
          position: "absolute",
          bottom: height * 0.12,
          left: 0,
          width: "100%",
          textAlign: "center",
          opacity: textOpacity,
          filter: `blur(${textBlur}px)`,
        }}
      >
        <div
          style={{
            fontFamily: FONTS.heading,
            fontSize: 48 * S,
            fontWeight: FONT_WEIGHTS.extrabold,
            color: COLORS.textPrimary,
            letterSpacing: "-0.025em",
          }}
        >
          A month of content. Minutes to make.
        </div>
      </div>
    </>
  );
};

// ---- Vignette B: Phone Mockup ----
const VignetteB: React.FC<{ localFrame: number; S: number; width: number; height: number }> = ({
  localFrame,
  S,
  width,
  height,
}) => {
  // Phone scales in
  const phoneProgress = interpolate(localFrame, [0, 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: luxEase,
  });
  const phoneScale = 0.97 + 0.03 * phoneProgress;
  const phoneOpacity = interpolate(localFrame, [0, 18], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Eyebrow
  const eyebrowOpacity = interpolate(localFrame, [20, 35], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Heading
  const headingOpacity = interpolate(localFrame, [35, 55], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: heroReveal,
  });
  const headingBlur = interpolate(localFrame, [35, 55], [8, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: heroReveal,
  });

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 80 * S,
      }}
    >
      {/* Phone */}
      <div
        style={{
          opacity: phoneOpacity,
          transform: `scale(${phoneScale})`,
        }}
      >
        <PhoneMockup width={240 * S} height={420 * S} />
      </div>

      {/* Text side */}
      <div style={{ maxWidth: 500 * S }}>
        <div
          style={{
            fontFamily: FONTS.mono,
            fontSize: 11 * S,
            fontWeight: FONT_WEIGHTS.medium,
            color: COLORS.accent,
            textTransform: "uppercase",
            letterSpacing: "0.25em",
            marginBottom: 16 * S,
            opacity: eyebrowOpacity,
          }}
        >
          SCROLL-STOPPING
        </div>
        <div
          style={{
            fontFamily: FONTS.heading,
            fontSize: 44 * S,
            fontWeight: FONT_WEIGHTS.extrabold,
            color: COLORS.textPrimary,
            letterSpacing: "-0.025em",
            lineHeight: 1.15,
            opacity: headingOpacity,
            filter: `blur(${headingBlur}px)`,
          }}
        >
          Every reel. Every carousel.
          <br />
          On brand.
        </div>
      </div>
    </div>
  );
};

// ---- Vignette C: Progress Bar + Percentage ----
const VignetteC: React.FC<{ localFrame: number; S: number; width: number; height: number }> = ({
  localFrame,
  S,
  width,
  height,
}) => {
  // Percentage 0→100 over 54 frames (1.8s)
  const percentage = Math.round(
    interpolate(localFrame, [0, 54], [0, 100], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: magneticSnap,
    }),
  );

  const progress = interpolate(localFrame, [0, 54], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: magneticSnap,
  });

  // Text appears at frame 60
  const textOpacity = interpolate(localFrame, [60, 80], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: heroReveal,
  });
  const textBlur = interpolate(localFrame, [60, 80], [8, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: heroReveal,
  });

  return (
    <>
      {/* Percentage */}
      <div
        style={{
          position: "absolute",
          top: height * 0.28,
          left: 0,
          width: "100%",
          textAlign: "center",
          fontFamily: FONTS.mono,
          fontSize: 120 * S,
          fontWeight: FONT_WEIGHTS.extrabold,
          color: COLORS.accent,
          letterSpacing: "-0.02em",
        }}
      >
        {percentage}%
      </div>

      {/* Progress bar */}
      <div
        style={{
          position: "absolute",
          top: height * 0.55,
          left: "50%",
          transform: "translateX(-50%)",
        }}
      >
        <ProgressBar
          progress={progress}
          width={500 * S}
          height={10 * S}
        />
      </div>

      {/* Text */}
      <div
        style={{
          position: "absolute",
          bottom: height * 0.15,
          left: 0,
          width: "100%",
          textAlign: "center",
          opacity: textOpacity,
          filter: `blur(${textBlur}px)`,
        }}
      >
        <div
          style={{
            fontFamily: FONTS.heading,
            fontSize: 48 * S,
            fontWeight: FONT_WEIGHTS.extrabold,
            color: COLORS.textPrimary,
            letterSpacing: "-0.025em",
          }}
        >
          You describe it. We generate it.
        </div>
      </div>
    </>
  );
};
