import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS, FONTS } from "../theme";

export interface ListItemProps {
  items: string[];
  /** Optional eyebrow / section label above the list. */
  label?: string;
  /** Numbering style: "decimal" (1.) or "none". */
  style?: "decimal" | "none";
}

export const ListItem: React.FC<ListItemProps> = ({ items, label, style = "decimal" }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const labelOpacity = interpolate(frame, [0, fps * 0.4], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: COLORS.bg.listItem }}>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          height: "100%",
          width: "100%",
          alignItems: "flex-start",
          justifyContent: "center",
          padding: "0 12%",
          gap: 28,
        }}
      >
        {label && (
          <div
            style={{
              fontFamily: FONTS.body,
              fontSize: 22,
              color: COLORS.text.secondary,
              letterSpacing: 4,
              textTransform: "uppercase",
              marginBottom: 20,
              opacity: labelOpacity,
            }}
          >
            {label}
          </div>
        )}
        {items.map((item, i) => {
          const delay = (i + 1) * fps * 0.25;
          const itemOpacity = interpolate(
            frame,
            [delay, delay + fps * 0.4],
            [0, 1],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
          );
          const shift = interpolate(frame, [delay, delay + fps * 0.4], [12, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          return (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "baseline",
                gap: 28,
                fontFamily: FONTS.body,
                fontSize: 44,
                color: COLORS.text.primary,
                opacity: itemOpacity,
                transform: `translateX(${shift}px)`,
              }}
            >
              {style === "decimal" && (
                <span
                  style={{
                    fontFamily: FONTS.mono,
                    fontSize: 32,
                    color: COLORS.text.accent,
                    minWidth: 48,
                  }}
                >
                  {String(i + 1).padStart(2, "0")}
                </span>
              )}
              <span style={{ lineHeight: 1.25 }}>{item}</span>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
