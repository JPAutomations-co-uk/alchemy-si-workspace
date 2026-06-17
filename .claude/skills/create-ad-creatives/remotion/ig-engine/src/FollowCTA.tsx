import React from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { COLORS, FONTS, FONT_WEIGHTS, RADII, getFontFaces } from "./utils/theme";
import { backOut, magneticSnap } from "./utils/easing";

export interface FollowCTAProps {
  username: string;
  profileImageSrc?: string;
  displayName?: string;
}

export const FollowCTA: React.FC<FollowCTAProps> = ({
  username = "jpautomations",
  profileImageSrc,
  displayName,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height, durationInFrames } = useVideoConfig();

  const scale = width / 1080;

  // ── Timeline (45 frames = 1.5s @ 30fps) ──
  const enterEnd = 9;
  const exitStart = durationInFrames - 12;

  // Card entrance: slide up + scale pop
  const enterProgress = interpolate(frame, [0, enterEnd], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: backOut,
  });

  // Card exit: slide down + fade
  const exitProgress = interpolate(
    frame,
    [exitStart, durationInFrames],
    [0, 1],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: magneticSnap,
    },
  );

  const translateY =
    (1 - enterProgress) * 120 * scale + exitProgress * 100 * scale;
  const cardScale = interpolate(enterProgress, [0, 1], [0.85, 1]) *
    interpolate(exitProgress, [0, 1], [1, 0.9]);
  const cardOpacity = enterProgress * (1 - exitProgress);

  // Follow button: delayed pop-in
  const btnProgress = interpolate(frame, [6, 14], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: backOut,
  });
  const btnScale = interpolate(btnProgress, [0, 1], [0.5, 1]);
  const btnOpacity = btnProgress;

  // Subtle glow pulse during hold
  const glowPhase = Math.sin((frame / fps) * Math.PI * 3) * 0.5 + 0.5;
  const glowOpacity = interpolate(glowPhase, [0, 1], [0.15, 0.4]);

  // Profile pic: subtle rotation wiggle on enter
  const picRotate = interpolate(frame, [3, 12], [-8, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: backOut,
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "transparent",
        display: "flex",
        alignItems: "flex-end",
        justifyContent: "center",
        paddingBottom: 280 * scale,
      }}
    >
      <style dangerouslySetInnerHTML={{ __html: getFontFaces() }} />

      {/* Card container */}
      <div
        style={{
          transform: `translateY(${translateY}px) scale(${cardScale})`,
          opacity: cardOpacity,
          display: "flex",
          alignItems: "center",
          gap: 18 * scale,
          background: "rgba(0, 0, 0, 0.55)",
          border: `1.5px solid rgba(255, 255, 255, 0.12)`,
          borderRadius: RADII.cardLg * scale,
          padding: `${16 * scale}px ${22 * scale}px ${16 * scale}px ${16 * scale}px`,
          backdropFilter: "blur(24px)",
          WebkitBackdropFilter: "blur(24px)",
          boxShadow: `
            0 8px 32px rgba(0, 0, 0, 0.4),
            0 0 0 1px rgba(255, 255, 255, 0.05),
            inset 0 1px 0 rgba(255, 255, 255, 0.08),
            0 0 ${40 * scale}px rgba(45, 212, 191, ${glowOpacity})
          `,
        }}
      >
        {/* Profile picture */}
        <div
          style={{
            width: 60 * scale,
            height: 60 * scale,
            borderRadius: "50%",
            overflow: "hidden",
            border: `2.5px solid ${COLORS.accent}`,
            flexShrink: 0,
            transform: `rotate(${picRotate}deg)`,
            boxShadow: `0 0 16px rgba(45, 212, 191, 0.3)`,
          }}
        >
          {profileImageSrc ? (
            <Img
              src={profileImageSrc}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
              }}
            />
          ) : (
            <div
              style={{
                width: "100%",
                height: "100%",
                background: `linear-gradient(135deg, ${COLORS.accent}, #6366F1)`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 26 * scale,
                fontFamily: FONTS.heading,
                fontWeight: FONT_WEIGHTS.bold,
                color: COLORS.textPrimary,
              }}
            >
              {username[0]?.toUpperCase()}
            </div>
          )}
        </div>

        {/* Username + display name */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 2 * scale,
          }}
        >
          {displayName && (
            <span
              style={{
                fontFamily: FONTS.heading,
                fontWeight: FONT_WEIGHTS.semibold,
                fontSize: 18 * scale,
                color: COLORS.textPrimary,
                lineHeight: 1.2,
              }}
            >
              {displayName}
            </span>
          )}
          <span
            style={{
              fontFamily: FONTS.heading,
              fontWeight: displayName
                ? FONT_WEIGHTS.regular
                : FONT_WEIGHTS.semibold,
              fontSize: (displayName ? 15 : 19) * scale,
              color: displayName ? COLORS.textMuted : COLORS.textPrimary,
              lineHeight: 1.2,
            }}
          >
            @{username}
          </span>
        </div>

        {/* Follow button */}
        <div
          style={{
            marginLeft: 8 * scale,
            transform: `scale(${btnScale})`,
            opacity: btnOpacity,
          }}
        >
          <div
            style={{
              background: COLORS.accent,
              borderRadius: RADII.pill,
              padding: `${10 * scale}px ${22 * scale}px`,
              fontFamily: FONTS.heading,
              fontWeight: FONT_WEIGHTS.bold,
              fontSize: 16 * scale,
              color: "#000000",
              letterSpacing: 0.3,
              whiteSpace: "nowrap",
              boxShadow: `0 0 20px rgba(45, 212, 191, ${glowOpacity * 0.8})`,
            }}
          >
            Follow
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
