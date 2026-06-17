import React from "react";
import { useCurrentFrame } from "remotion";
import { beatPulseScale } from "../utils/beat";

interface BeatPulseProps {
  children: React.ReactNode;
  active: boolean;
  amplitude?: number;
  style?: React.CSSProperties;
}

export const BeatPulse: React.FC<BeatPulseProps> = ({
  children,
  active,
  amplitude = 0.006,
  style,
}) => {
  const frame = useCurrentFrame();
  const scale = active ? beatPulseScale(frame, amplitude) : 1;

  return (
    <div
      style={{
        transform: `scale(${scale})`,
        willChange: "transform",
        ...style,
      }}
    >
      {children}
    </div>
  );
};
