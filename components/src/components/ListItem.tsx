import React from "react";
import { AbsoluteFill, useVideoConfig } from "remotion";
import { AccentFx, type AccentFxMode } from "../motion/AccentFx";
import { TextMotion, type TextMotionMode } from "../motion/TextMotion";
import { PALETTES, type Palette } from "../theme";
import {
  FONT_STACK, FONT_WEIGHT,
  LETTER_SPACING, LINE_HEIGHT, SIZE, TYPE_RATIO,
} from "../tokens";

export interface ListItemProps {
  items: string[];
  label?: string;
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
  const { fps, height } = useVideoConfig();
  const itemSize = Math.round(height * TYPE_RATIO.value);
  const labelSize = Math.round(height * TYPE_RATIO.label);
  const numeralSize = Math.round(height * TYPE_RATIO.numeral);
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
          padding: `0 ${SIZE[10]}px`,
          gap: SIZE[5],
        }}
      >
        {label && (
          <TextMotion mode="fade">
            <div
              style={{
                fontFamily: FONT_STACK.mono,
                fontSize: labelSize,
                fontWeight: FONT_WEIGHT[5],
                color: palette.accent,
                letterSpacing: LETTER_SPACING[6],
                textTransform: "uppercase",
                marginBottom: SIZE[2],
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
            gap: SIZE[6],
            fontFamily: FONT_STACK.body,
            fontSize: itemSize,
            fontWeight: FONT_WEIGHT[4],
            color: palette.text,
            lineHeight: LINE_HEIGHT[3],
          };
          const content = isCharMode ? (
            <span><TextMotion mode={text_motion} text={item} startFrame={startFrame} /></span>
          ) : (
            <TextMotion mode={text_motion} startFrame={startFrame}>
              <span>{item}</span>
            </TextMotion>
          );
          return (
            <div key={i} style={itemTextStyle}>
              {style === "decimal" && (
                <span
                  style={{
                    fontFamily: FONT_STACK.mono,
                    fontSize: numeralSize,
                    fontWeight: FONT_WEIGHT[5],
                    color: palette.accent,
                    minWidth: numeralSize * 1.6,
                    letterSpacing: LETTER_SPACING[3],
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
