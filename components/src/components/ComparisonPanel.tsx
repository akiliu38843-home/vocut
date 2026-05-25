import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS, FONTS } from "../theme";

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
  /** Custom backgrounds. Falls back to theme defaults. */
  leftBg?: string;
  rightBg?: string;
}

export const ComparisonPanel: React.FC<ComparisonPanelProps> = ({
  title,
  items,
  leftBg,
  rightBg,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const panelOpacity = interpolate(frame, [0, fps * 0.5], [0, 1], { extrapolateRight: "clamp" });
  const ruleProgress = interpolate(frame, [fps * 0.5, fps * 1.2], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const itemBackgrounds =
    items.length === 2
      ? [leftBg || COLORS.bg.comparisonLeft, rightBg || COLORS.bg.comparisonRight]
      : items.map((_, i) =>
          i % 2 === 0 ? COLORS.bg.comparisonLeft : COLORS.bg.comparisonRight,
        );

  return (
    <AbsoluteFill style={{ background: "#000" }}>
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
            color: COLORS.text.secondary,
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
                background: itemBackgrounds[i],
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                padding: "0 4%",
                opacity: itemOpacity,
                borderRight:
                  i < items.length - 1
                    ? `1px solid ${COLORS.text.quiet}`
                    : undefined,
              }}
            >
              {it.label && (
                <div
                  style={{
                    fontFamily: FONTS.body,
                    fontSize: 22,
                    color: COLORS.text.secondary,
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
                  color: COLORS.text.primary,
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
                    color: COLORS.text.accent,
                  }}
                >
                  {it.tag}
                </div>
              )}
            </div>
          );
        })}
      </div>
      {/* Center axis rule, draws downward */}
      {items.length === 2 && (
        <div
          style={{
            position: "absolute",
            left: "50%",
            top: "20%",
            height: `${ruleProgress * 60}%`,
            width: 1,
            background: COLORS.text.quiet,
            transform: "translateX(-0.5px)",
          }}
        />
      )}
    </AbsoluteFill>
  );
};
