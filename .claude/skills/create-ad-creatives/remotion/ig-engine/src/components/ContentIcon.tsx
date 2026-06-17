import React from "react";
import { COLORS, FONTS, FONT_WEIGHTS } from "../utils/theme";

interface ContentIconProps {
  label: string;
  marker?: string;
  fontSize?: number;
  style?: React.CSSProperties;
}

export const ContentIcon: React.FC<ContentIconProps> = ({
  label,
  marker = "[+]",
  fontSize = 14,
  style,
}) => {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: fontSize * 0.75,
        background: COLORS.cardBg,
        border: `1px solid ${COLORS.cardBorder}`,
        borderRadius: 12,
        padding: `${fontSize * 0.85}px ${fontSize * 1.2}px`,
        ...style,
      }}
    >
      <span
        style={{
          fontFamily: FONTS.mono,
          fontSize: fontSize * 0.9,
          color: COLORS.accent,
          fontWeight: FONT_WEIGHTS.medium,
          lineHeight: 1,
        }}
      >
        {marker}
      </span>
      <span
        style={{
          fontFamily: FONTS.body,
          fontSize,
          color: COLORS.textMuted,
          fontWeight: FONT_WEIGHTS.medium,
          letterSpacing: "-0.01em",
        }}
      >
        {label}
      </span>
    </div>
  );
};
