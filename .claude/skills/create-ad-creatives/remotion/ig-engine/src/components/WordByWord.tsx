import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { heroReveal } from "../utils/easing";
import { FONTS, FONT_WEIGHTS, COLORS } from "../utils/theme";

interface WordByWordProps {
  text: string;
  startFrame: number;
  frameBetweenWords?: number;
  wordDuration?: number;
  fontSize?: number;
  style?: React.CSSProperties;
}

export const WordByWord: React.FC<WordByWordProps> = ({
  text,
  startFrame,
  frameBetweenWords = 14,
  wordDuration = 24,
  fontSize = 72,
  style,
}) => {
  const frame = useCurrentFrame();
  const words = text.split(" ");

  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        gap: fontSize * 0.35,
        fontFamily: FONTS.heading,
        fontWeight: FONT_WEIGHTS.extrabold,
        fontSize,
        letterSpacing: "-0.025em",
        color: COLORS.textPrimary,
        ...style,
      }}
    >
      {words.map((word, i) => {
        const wordStart = startFrame + i * frameBetweenWords;
        const opacity = interpolate(
          frame,
          [wordStart, wordStart + wordDuration * 0.5],
          [0, 1],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: heroReveal },
        );
        const blur = interpolate(
          frame,
          [wordStart, wordStart + wordDuration],
          [6, 0],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: heroReveal },
        );
        const y = interpolate(
          frame,
          [wordStart, wordStart + wordDuration],
          [10, 0],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: heroReveal },
        );

        return (
          <span
            key={i}
            style={{
              opacity,
              filter: `blur(${blur}px)`,
              transform: `translateY(${y}px)`,
              display: "inline-block",
            }}
          >
            {word}
          </span>
        );
      })}
    </div>
  );
};
