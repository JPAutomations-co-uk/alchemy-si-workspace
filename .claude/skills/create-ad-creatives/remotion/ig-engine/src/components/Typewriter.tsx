import React from "react";
import { useCurrentFrame } from "remotion";
import { FONTS, COLORS } from "../utils/theme";

interface TypewriterProps {
  text: string;
  startFrame: number;
  charsPerFrame?: number;
  showCursor?: boolean;
  cursorBlinkFrames?: number;
  fontSize?: number;
  style?: React.CSSProperties;
}

export const Typewriter: React.FC<TypewriterProps> = ({
  text,
  startFrame,
  charsPerFrame = 0.5,
  showCursor = true,
  cursorBlinkFrames = 23,
  fontSize = 80,
  style,
}) => {
  const frame = useCurrentFrame();
  const elapsed = Math.max(0, frame - startFrame);
  const visibleChars = Math.min(text.length, Math.floor(elapsed * charsPerFrame));
  const displayText = text.substring(0, visibleChars);
  const isTyping = visibleChars < text.length && elapsed > 0;
  const cursorVisible =
    showCursor && (isTyping || Math.floor(elapsed / (cursorBlinkFrames / 2)) % 2 === 0);

  return (
    <span
      style={{
        fontFamily: FONTS.mono,
        fontSize,
        color: COLORS.accent,
        letterSpacing: "-0.02em",
        fontWeight: 700,
        ...style,
      }}
    >
      {displayText}
      {cursorVisible && elapsed > 0 && (
        <span style={{ opacity: 0.8, marginLeft: 2 }}>|</span>
      )}
    </span>
  );
};
