import React from "react";
import { COLORS, RADII } from "../utils/theme";

interface GlassmorphismCardProps {
  children: React.ReactNode;
  borderRadius?: number;
  padding?: string;
  glowing?: boolean;
  style?: React.CSSProperties;
}

export const GlassmorphismCard: React.FC<GlassmorphismCardProps> = ({
  children,
  borderRadius = RADII.card,
  padding = "24px 22px",
  glowing = false,
  style,
}) => {
  return (
    <div
      style={{
        background: COLORS.cardBg,
        border: `1px solid ${glowing ? COLORS.cardBorderActive : COLORS.cardBorder}`,
        borderRadius,
        padding,
        backdropFilter: "blur(16px)",
        WebkitBackdropFilter: "blur(16px)",
        boxShadow: glowing
          ? `0 20px 60px ${COLORS.cardGlow}`
          : "none",
        transition: "border-color 0.5s, box-shadow 0.5s",
        ...style,
      }}
    >
      {children}
    </div>
  );
};
