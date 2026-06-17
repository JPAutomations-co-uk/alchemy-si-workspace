export const COLORS = {
  bg: "#000000",
  accent: "#2DD4BF",
  accentLight: "#99F6E4",
  textPrimary: "#FFFFFF",
  textMuted: "#9CA3AF",
  textDim: "#6B7280",
  textSubtle: "#D1D5DB",
  cardBg: "rgba(255,255,255,0.02)",
  cardBorder: "rgba(255,255,255,0.1)",
  cardBorderActive: "rgba(45,212,191,0.18)",
  cardGlow: "rgba(45,212,191,0.1)",
  tealDim: "rgba(45,212,191,0.06)",
  tealGlow: "rgba(45,212,191,0.25)",
  gridLine: "rgba(128,128,128,0.07)",
} as const;

export const FONTS = {
  heading: "'Geist Sans', 'Inter', system-ui, sans-serif",
  body: "'Geist Sans', 'Inter', system-ui, sans-serif",
  mono: "'Geist Mono', 'SF Mono', monospace",
} as const;

export const FONT_WEIGHTS = {
  regular: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
  extrabold: 900, // Geist "Black" weight
} as const;

export const RADII = {
  card: 16,
  cardLg: 24,
  pill: 100,
} as const;

/**
 * Font face declarations for Geist fonts.
 * Individual weight files for Sans, variable font for Mono.
 * Files in public/fonts/.
 */
export function getFontFaces(): string {
  const sansWeights = [
    { weight: 400, file: "Geist-Regular.woff2" },
    { weight: 500, file: "Geist-Medium.woff2" },
    { weight: 600, file: "Geist-SemiBold.woff2" },
    { weight: 700, file: "Geist-Bold.woff2" },
    { weight: 900, file: "Geist-Black.woff2" },
  ];

  const sansFaces = sansWeights
    .map(
      (w) => `
    @font-face {
      font-family: 'Geist Sans';
      src: url('/static/fonts/${w.file}') format('woff2');
      font-weight: ${w.weight};
      font-display: swap;
    }`,
    )
    .join("\n");

  return `
    ${sansFaces}
    @font-face {
      font-family: 'Geist Mono';
      src: url('/static/fonts/GeistMonoVF.woff2') format('woff2');
      font-weight: 100 900;
      font-display: swap;
    }
  `;
}
