import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";

interface GradientMeshProps {
  intensity: number; // 0-1: how bright the teal orbs are
  warmth: number; // 0-1: adds warm stress tint (for scene 1 tension)
}

const ORBS = [
  { cx: 0.38, cy: 0.32, r: 0.55, speed: 0.8 },
  { cx: 0.72, cy: 0.68, r: 0.4, speed: 1.1 },
  { cx: 0.85, cy: 0.18, r: 0.3, speed: 1.4 },
  { cx: 0.15, cy: 0.75, r: 0.35, speed: 0.6 },
];

export const GradientMesh: React.FC<GradientMeshProps> = ({
  intensity,
  warmth,
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const phase = frame * 0.0083;

  return (
    <AbsoluteFill style={{ zIndex: 0 }}>
      {ORBS.map((orb, i) => {
        const x =
          orb.cx * width + Math.sin(phase * orb.speed + i * 1.5) * width * 0.1;
        const y =
          orb.cy * height +
          Math.cos(phase * orb.speed * 0.7 + i * 2) * height * 0.08;
        const size = orb.r * Math.min(width, height);
        const alpha = intensity * (i === 0 ? 1.0 : i === 1 ? 0.35 : 0.2);

        // Base teal, with optional warm shift
        const r = Math.round(45 + warmth * 80);
        const g = Math.round(212 - warmth * 80);
        const b = Math.round(191 - warmth * 60);

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x - size,
              top: y - size,
              width: size * 2,
              height: size * 2,
              borderRadius: "50%",
              background: `radial-gradient(circle, rgba(${r},${g},${b},${alpha}) 0%, transparent 70%)`,
              filter: `blur(${size * 0.6}px)`,
              willChange: "transform",
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
