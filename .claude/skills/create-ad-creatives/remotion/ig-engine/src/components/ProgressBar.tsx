import React from "react";
import { COLORS, RADII } from "../utils/theme";

interface ProgressBarProps {
  progress: number; // 0-1
  width?: number;
  height?: number;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  width = 460,
  height = 8,
}) => {
  return (
    <div
      style={{
        width,
        height,
        borderRadius: RADII.pill,
        background: "rgba(255,255,255,0.05)",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          width: `${progress * 100}%`,
          height: "100%",
          borderRadius: RADII.pill,
          background: `linear-gradient(90deg, ${COLORS.accent}, rgba(45,212,191,0.4))`,
        }}
      />
    </div>
  );
};
