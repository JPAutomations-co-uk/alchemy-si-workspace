import React from "react";
import { AbsoluteFill, useVideoConfig } from "remotion";

interface GridOverlayProps {
  opacity: number;
}

export const GridOverlay: React.FC<GridOverlayProps> = ({ opacity }) => {
  const { width } = useVideoConfig();
  const cellSize = Math.round(32 * (width / 1920));

  return (
    <AbsoluteFill
      style={{
        backgroundImage: `linear-gradient(to right, rgba(128,128,128,0.07) 1px, transparent 1px), linear-gradient(to bottom, rgba(128,128,128,0.07) 1px, transparent 1px)`,
        backgroundSize: `${cellSize}px ${cellSize}px`,
        opacity,
        zIndex: 1,
        maskImage:
          "radial-gradient(ellipse 80% 70% at 50% 50%, black 30%, transparent 100%)",
        WebkitMaskImage:
          "radial-gradient(ellipse 80% 70% at 50% 50%, black 30%, transparent 100%)",
      }}
    />
  );
};
