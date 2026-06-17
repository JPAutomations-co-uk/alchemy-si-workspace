import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { COLORS } from "../utils/theme";

interface PhoneMockupProps {
  width?: number;
  height?: number;
}

export const PhoneMockup: React.FC<PhoneMockupProps> = ({
  width = 280,
  height = 500,
}) => {
  const frame = useCurrentFrame();

  // Animated gradient inside the phone screen
  const gradientPos = interpolate(frame, [0, 90], [0, 100], {
    extrapolateRight: "extend",
  });

  return (
    <div
      style={{
        width,
        height,
        borderRadius: 32,
        border: `2px solid ${COLORS.cardBorder}`,
        background: COLORS.bg,
        overflow: "hidden",
        position: "relative",
      }}
    >
      {/* Notch */}
      <div
        style={{
          position: "absolute",
          top: 8,
          left: "50%",
          transform: "translateX(-50%)",
          width: width * 0.35,
          height: 24,
          borderRadius: 12,
          background: COLORS.bg,
          border: `1px solid ${COLORS.cardBorder}`,
          zIndex: 2,
        }}
      />
      {/* Animated screen content */}
      <div
        style={{
          position: "absolute",
          inset: 4,
          borderRadius: 28,
          background: `linear-gradient(${gradientPos}deg, rgba(45,212,191,0.15) 0%, rgba(45,212,191,0.05) 40%, rgba(0,0,0,0.9) 100%)`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {/* Play triangle */}
        <div
          style={{
            width: 0,
            height: 0,
            borderLeft: "24px solid rgba(255,255,255,0.6)",
            borderTop: "14px solid transparent",
            borderBottom: "14px solid transparent",
            marginLeft: 6,
          }}
        />
      </div>
    </div>
  );
};
