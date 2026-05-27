import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { AccentFx, type AccentFxMode } from "../motion/AccentFx";
import { TextMotion, type TextMotionMode } from "../motion/TextMotion";
import { PALETTES, type Palette } from "../theme";
import {
  FONT_STACK, FONT_WEIGHT,
  LETTER_SPACING, LINE_HEIGHT, SIZE, TYPE_RATIO,
} from "../tokens";

export interface KeyNumberProps {
  primary: string;
  unit?: string;
  label?: string;
  secondary?: string;
  palette?: Palette;
  text_motion?: TextMotionMode;
  accent_fx?: AccentFxMode;
}

export const KeyNumber: React.FC<KeyNumberProps> = ({
  primary,
  unit,
  label,
  secondary,
  palette = PALETTES.editorial_dark,
  text_motion = "scale_in",
  accent_fx = "none",
}) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  // 主数字按"屏高 16%"算（行业 hero data scene 标准）
  const primarySize = Math.round(height * TYPE_RATIO.giant);
  const labelSize = Math.round(height * TYPE_RATIO.label);
  const unitOpacity = interpolate(frame, [fps * 0.4, fps * 0.7], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const labelOpacity = interpolate(frame, [fps * 0.7, fps * 1.0], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const primaryStyle: React.CSSProperties = {
    fontFamily: FONT_STACK.display,
    fontSize: primarySize,
    fontWeight: FONT_WEIGHT[6],
    color: palette.accent,
    lineHeight: LINE_HEIGHT[0],
    letterSpacing: LETTER_SPACING[0],
    textShadow: `0 2px 24px ${palette.accent}33`,
  };

  // Dedup: if the LLM put the unit into the primary already (e.g. "60亿日元"
  // + unit="日元"), drop the trailing unit to avoid "60亿日元日元".
  const cleanUnit = unit && primary.trim().endsWith(unit.trim()) ? undefined : unit;

  const isCharMode = text_motion === "typewriter" || text_motion === "wave";
  const primaryEl = isCharMode ? (
    <span style={primaryStyle}><TextMotion mode={text_motion} text={primary} /></span>
  ) : (
    <TextMotion mode={text_motion}><span style={primaryStyle}>{primary}</span></TextMotion>
  );

  // Underline rule scales with the primary text — wider for short tokens,
  // narrower for long ones, but never longer than the number itself.
  const ruleWidth = Math.min(
    Math.max(primary.length * primarySize * 0.85, primarySize * 1.5),
    primarySize * 6,
  );

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
          gap: SIZE[4],
        }}
      >
        {/* 小标签在数字上方 —— 像图表标题 */}
        {label && (
          <TextMotion mode="fade">
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
              {label}
            </div>
          </TextMotion>
        )}
        {/* 大数字 + 单位 */}
        <div style={{ display: "flex", alignItems: "baseline", gap: SIZE[3] }}>
          <AccentFx mode={accent_fx} palette={palette}>{primaryEl}</AccentFx>
          {cleanUnit && (
            <span
              style={{
                fontFamily: FONT_STACK.body,
                fontSize: primarySize * 0.35,
                fontWeight: FONT_WEIGHT[3],
                color: palette.text,
                opacity: unitOpacity,
              }}
            >
              {cleanUnit}
            </span>
          )}
        </div>
        {/* 装饰横线 —— 宽度跟随主文字 */}
        <div
          style={{
            width: ruleWidth,
            height: 2,
            background: palette.text,
            opacity: 0.3,
            marginTop: SIZE[2],
          }}
        />
        {secondary && (
          <p
            style={{
              margin: 0,
              fontFamily: FONT_STACK.mono,
              fontSize: labelSize,
              color: palette.quiet,
              opacity: labelOpacity,
              letterSpacing: LETTER_SPACING[3],
            }}
          >
            {secondary}
          </p>
        )}
      </div>
    </AbsoluteFill>
  );
};
