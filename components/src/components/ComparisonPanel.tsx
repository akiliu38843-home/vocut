import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { FONTS, PALETTES, type Palette } from "../theme";

export interface ComparisonItem {
  label?: string;
  value: string;
  tag?: string;
}

export interface ComparisonPanelProps {
  /** Optional title above the panels (e.g. "公测 vs 当下"). */
  title?: string;
  /** Two-way comparison default; three-way also supported. */
  items: ComparisonItem[];
  palette?: Palette;
  text_motion?: string;
  accent_fx?: string;
}

export const ComparisonPanel: React.FC<ComparisonPanelProps> = ({
  title,
  items,
  palette = PALETTES.editorial_dark,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const panelOpacity = interpolate(frame, [0, fps * 0.5], [0, 1], { extrapolateRight: "clamp" });
  const ruleProgress = interpolate(frame, [fps * 0.5, fps * 1.2], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Alternate surface tones for adjacent panels (subtle separation).
  const surfaces = items.map((_, i) =>
    i % 2 === 0 ? palette.bg : palette.surface,
  );

  return (
    <AbsoluteFill>
      {title && (
        <div
          style={{
            position: "absolute",
            top: 48,
            left: 0,
            right: 0,
            textAlign: "center",
            fontFamily: FONTS.body,
            fontSize: 28,
            color: palette.textSecondary,
            letterSpacing: 4,
            textTransform: "uppercase",
            opacity: panelOpacity,
            zIndex: 2,
          }}
        >
          {title}
        </div>
      )}
      <div style={{ display: "flex", height: "100%", width: "100%" }}>
        {items.map((it, i) => {
          const itemDelay = i * fps * 0.15;
          const itemOpacity = interpolate(
            frame,
            [itemDelay, itemDelay + fps * 0.5],
            [0, 1],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
          );
          return (
            <div
              key={i}
              style={{
                flex: 1,
                background: surfaces[i],
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                padding: "0 4%",
                opacity: itemOpacity,
                borderRight:
                  i < items.length - 1
                    ? `1px solid ${palette.quiet}`
                    : undefined,
              }}
            >
              {it.label && (
                <div
                  style={{
                    fontFamily: FONTS.body,
                    fontSize: 22,
                    color: palette.textSecondary,
                    letterSpacing: 3,
                    textTransform: "uppercase",
                    marginBottom: 28,
                  }}
                >
                  {it.label}
                </div>
              )}
              <div
                style={{
                  fontFamily: FONTS.display,
                  fontSize: "clamp(48px, 6vw, 84px)",
                  color: palette.text,
                  fontWeight: 400,
                  textAlign: "center",
                  lineHeight: 1.15,
                }}
              >
                {it.value}
              </div>
              {it.tag && (
                <div
                  style={{
                    marginTop: 24,
                    fontFamily: FONTS.mono,
                    fontSize: 22,
                    color: palette.accent,
                  }}
                >
                  {it.tag}
                </div>
              )}
            </div>
          );
        })}
      </div>
      {items.length === 2 && (
        <div
          style={{
            position: "absolute",
            left: "50%",
            top: "20%",
            height: `${ruleProgress * 60}%`,
            width: 1,
            background: palette.quiet,
            transform: "translateX(-0.5px)",
          }}
        />
      )}
    </AbsoluteFill>
  );
};
