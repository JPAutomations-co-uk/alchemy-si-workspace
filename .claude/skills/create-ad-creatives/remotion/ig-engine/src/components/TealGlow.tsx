import React from "react";

interface TealGlowProps {
  x: string;
  y: string;
  size: number;
  opacity: number;
}

export const TealGlow: React.FC<TealGlowProps> = ({ x, y, size, opacity }) => {
  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        width: size * 2,
        height: size * 2,
        borderRadius: "50%",
        background: "#2DD4BF",
        filter: `blur(${size}px)`,
        opacity,
        transform: "translate(-50%, -50%)",
        pointerEvents: "none",
      }}
    />
  );
};
