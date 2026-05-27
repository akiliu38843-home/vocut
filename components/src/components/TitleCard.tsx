import React from "react";
import { AbsoluteFill, useVideoConfig } from "remotion";
import { AccentFx, type AccentFxMode } from "../motion/AccentFx";
import { TextMotion, type TextMotionMode } from "../motion/TextMotion";
import { PALETTES, type Palette } from "../theme";
import {
  FONT_SIZE, FONT_STACK, FONT_WEIGHT,
  LETTER_SPACING, LINE_HEIGHT, SIZE,
} from "../tokens";

export interface TitleCardProps {
  title: string;
  subtitle?: string;
  eyebrow?: string;
  palette?: Palette;
  text_motion?: TextMotionMode;
  accent_fx?: AccentFxMode;
}

export const TitleCard: React.FC<TitleCardProps> = ({
  title,
  subtitle,
  eyebrow,
  palette = PALETTES.editorial_dark,
  text_motion = "fade",
  accent_fx = "none",
}) => {
  const { fps, width } = useVideoConfig();
  // 大屏用大字 (FONT_SIZE 9), 竖屏用中字 (FONT_SIZE 7)
  const titleSize = width >= 1280 ? FONT_SIZE[9] : FONT_SIZE[7];
  const isCharMode = text_motion === "typewriter" || text_motion === "wave";

  const titleStyle: React.CSSProperties = {
    margin: 0,
    fontFamily: FONT_STACK.display,
    fontWeight: FONT_WEIGHT[5],
    fontSize: titleSize,
    color: palette.text,
    lineHeight: LINE_HEIGHT[1],
    letterSpacing: LETTER_SPACING[1],
    // 极轻的文字阴影 — 让字"贴而不死"
    textShadow: `0 1px 0 ${palette.bg}, 0 2px 16px ${palette.bg}66`,
  };

  const titleEl = isCharMode ? (
    <h1 style={titleStyle}><TextMotion mode={text_motion} text={title} /></h1>
  ) : (
    <TextMotion mode={text_motion}><h1 style={titleStyle}>{title}</h1></TextMotion>
  );

  return (
    <AbsoluteFill>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          height: "100%",
          width: "100%",
          alignItems: "flex-start",      // 左对齐（不再死磕居中）
          justifyContent: "center",
          padding: `0 ${SIZE[10]}px`,    // Open Props size-10 = 80px
          gap: SIZE[5],                   // 24px
        }}
      >
        {eyebrow && (
          <TextMotion mode="fade">
            <div
              style={{
                fontFamily: FONT_STACK.mono,
                fontSize: FONT_SIZE[1],
                fontWeight: FONT_WEIGHT[5],
                color: palette.accent,
                letterSpacing: LETTER_SPACING[6],
                textTransform: "uppercase",
              }}
            >
              {eyebrow}
            </div>
          </TextMotion>
        )}
        <AccentFx mode={accent_fx} palette={palette}>{titleEl}</AccentFx>
        {/* 装饰横线：紧贴标题下方，宽度=标题字号的 1.5 倍 —— 锚住，不浮空 */}
        <TextMotion mode="fade">
          <div
            style={{
              width: titleSize * 1.5,
              height: 2,
              background: palette.accent,
              marginTop: SIZE[2],
            }}
          />
        </TextMotion>
        {subtitle && (
          <TextMotion mode="fade">
            <p
              style={{
                margin: 0,
                fontFamily: FONT_STACK.body,
                fontSize: FONT_SIZE[3],
                fontWeight: FONT_WEIGHT[4],
                color: palette.textSecondary,
                lineHeight: LINE_HEIGHT[4],
                letterSpacing: LETTER_SPACING[2],
                maxWidth: "70%",
              }}
            >
              {subtitle}
            </p>
          </TextMotion>
        )}
      </div>
    </AbsoluteFill>
  );
};
