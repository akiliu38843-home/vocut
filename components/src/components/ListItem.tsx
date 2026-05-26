import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { AccentFx, type AccentFxMode } from "../motion/AccentFx";
import { TextMotion, type TextMotionMode } from "../motion/TextMotion";
import { FONTS, PALETTES, type Palette } from "../theme";

export interface ListItemProps {
  items: string[];
  /** Optional eyebrow / section label above the list. */
  label?: string;
  /** Numbering style. */
  style?: "decimal" | "none";
  palette?: Palette;
  text_motion?: TextMotionMode;
  accent_fx?: AccentFxMode;
}

export const ListItem: React.FC<ListItemProps> = ({
  items,
  label,
  style = "decimal",
  palette = PALETTES.editorial_dark,
  text_motion = "fade",
  accent_fx = "none",
}) => {
  const { fps } = useVideoConfig();

  const isCharMode = text_motion === "typewriter" || text_motion === "wave";

  return (
    <AbsoluteFill>
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
          <TextMotion mode="fade" durationFrames={Math.round(fps * 0.4)}>
            <div
              style={{
                fontFamily: FONTS.body,
                fontSize: 22,
                color: palette.textSecondary,
                letterSpacing: 4,
                textTransform: "uppercase",
                marginBottom: 20,
              }}
            >
              {label}
            </div>
          </TextMotion>
        )}
        {items.map((item, i) => {
          const startFrame = Math.round((i + 1) * fps * 0.25);
          const itemTextStyle: React.CSSProperties = {
            display: "flex",
            alignItems: "baseline",
            gap: 28,
            fontFamily: FONTS.body,
            fontSize: 44,
            color: palette.text,
          };
          // Per-item rendering: number + content
          const content = isCharMode ? (
            <span>
              <TextMotion mode={text_motion} text={item} startFrame={startFrame} />
            </span>
          ) : (
            <TextMotion mode={text_motion} startFrame={startFrame}>
              <span style={{ lineHeight: 1.25 }}>{item}</span>
            </TextMotion>
          );
          return (
            <div key={i} style={itemTextStyle}>
              {style === "decimal" && (
                <span
                  style={{
                    fontFamily: FONTS.mono,
                    fontSize: 32,
                    color: palette.accent,
                    minWidth: 48,
                  }}
                >
                  {String(i + 1).padStart(2, "0")}
                </span>
              )}
              <AccentFx mode={accent_fx} palette={palette} startFrame={startFrame}>
                {content}
              </AccentFx>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
