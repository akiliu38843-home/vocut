import React from "react";
import { AbsoluteFill, useVideoConfig } from "remotion";
import { AccentFx, type AccentFxMode } from "../motion/AccentFx";
import { TextMotion, type TextMotionMode } from "../motion/TextMotion";
import { PALETTES, type Palette } from "../theme";
import {
  FONT_STACK, FONT_WEIGHT,
  LETTER_SPACING, LINE_HEIGHT, SIZE, TYPE_RATIO,
} from "../tokens";

export interface ComparisonItem {
  label?: string;
  value: string;
  tag?: string;
}

export interface ComparisonPanelProps {
  title?: string;
  items: ComparisonItem[];
  palette?: Palette;
  text_motion?: TextMotionMode;
  accent_fx?: AccentFxMode;
}

export const ComparisonPanel: React.FC<ComparisonPanelProps> = ({
  title,
  items,
  palette = PALETTES.editorial_dark,
  text_motion = "fade",
  accent_fx = "none",
}) => {
  const { fps, height } = useVideoConfig();
  const valueSize = Math.round(height * TYPE_RATIO.primary);
  const labelSize = Math.round(height * TYPE_RATIO.label);
  const tagSize = Math.round(height * TYPE_RATIO.caption);
  const isCharMode = text_motion === "typewriter" || text_motion === "wave";

  return (
    <AbsoluteFill>
      {title && (
        <TextMotion mode="fade">
          <div
            style={{
              position: "absolute",
              top: SIZE[10],
              left: SIZE[10],
              right: SIZE[10],
              fontFamily: FONT_STACK.mono,
              fontSize: labelSize,
              fontWeight: FONT_WEIGHT[5],
              color: palette.accent,
              letterSpacing: LETTER_SPACING[6],
              textTransform: "uppercase",
              zIndex: 2,
            }}
          >
            {title}
          </div>
        </TextMotion>
      )}
      <div style={{ display: "flex", height: "100%", width: "100%" }}>
        {items.map((it, i) => {
          const itemStartFrame = Math.round(i * fps * 0.15);
          const valueStyle: React.CSSProperties = {
            fontFamily: FONT_STACK.display,
            fontSize: valueSize,
            fontWeight: FONT_WEIGHT[6],
            color: palette.text,
            lineHeight: LINE_HEIGHT[1],
            letterSpacing: LETTER_SPACING[1],
            textShadow: `0 1px 12px ${palette.bg}aa`,
          };
          const valueEl = isCharMode ? (
            <div style={valueStyle}>
              <TextMotion mode={text_motion} text={it.value} startFrame={itemStartFrame} />
            </div>
          ) : (
            <TextMotion mode={text_motion} startFrame={itemStartFrame}>
              <div style={valueStyle}>{it.value}</div>
            </TextMotion>
          );
          return (
            <div
              key={i}
              style={{
                flex: 1,
                background: i % 2 === 0 ? palette.bg : palette.surface,
                display: "flex",
                flexDirection: "column",
                alignItems: "flex-start",
                justifyContent: "center",
                padding: `0 ${SIZE[8]}px`,
                gap: SIZE[4],
              }}
            >
              {it.label && (
                <TextMotion mode="fade" startFrame={itemStartFrame}>
                  <div
                    style={{
                      fontFamily: FONT_STACK.mono,
                      fontSize: labelSize,
                      fontWeight: FONT_WEIGHT[5],
                      color: palette.textSecondary,
                      letterSpacing: LETTER_SPACING[6],
                      textTransform: "uppercase",
                    }}
                  >
                    {it.label}
                  </div>
                </TextMotion>
              )}
              <AccentFx mode={accent_fx} palette={palette} startFrame={itemStartFrame}>
                {valueEl}
              </AccentFx>
              {it.tag && (
                <TextMotion mode="fade" startFrame={itemStartFrame + Math.round(fps * 0.3)}>
                  <div
                    style={{
                      fontFamily: FONT_STACK.body,
                      fontSize: tagSize,
                      color: palette.accent,
                      letterSpacing: LETTER_SPACING[3],
                    }}
                  >
                    {it.tag}
                  </div>
                </TextMotion>
              )}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
