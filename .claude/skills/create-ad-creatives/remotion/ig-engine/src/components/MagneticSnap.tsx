import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { magneticSnap } from "../utils/easing";

interface MagneticSnapProps {
  children: React.ReactNode;
  startFrame: number;
  duration?: number;
  fromScale?: number;
  fromY?: number;
  fromX?: number;
  style?: React.CSSProperties;
}

export const MagneticSnap: React.FC<MagneticSnapProps> = ({
  children,
  startFrame,
  duration = 18,
  fromScale = 0.95,
  fromY = 0,
  fromX = 0,
  style,
}) => {
  const frame = useCurrentFrame();

  const progress = interpolate(frame, [startFrame, startFrame + duration], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: magneticSnap,
  });

  const opacity = interpolate(frame, [startFrame, startFrame + duration * 0.6], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const scale = fromScale + (1 - fromScale) * progress;
  const translateY = fromY * (1 - progress);
  const translateX = fromX * (1 - progress);

  return (
    <div
      style={{
        opacity,
        transform: `translate(${translateX}px, ${translateY}px) scale(${scale})`,
        willChange: "transform, opacity",
        ...style,
      }}
    >
      {children}
    </div>
  );
};
