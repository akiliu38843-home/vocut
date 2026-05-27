import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { AccentFx, type AccentFxMode } from "../motion/AccentFx";
import { TextMotion, type TextMotionMode } from "../motion/TextMotion";
import { PALETTES, type Palette } from "../theme";
import {
  FONT_SIZE, FONT_STACK, FONT_WEIGHT,
  LETTER_SPACING, LINE_HEIGHT, SIZE,
} from "../tokens";

export interface PullQuoteProps {
  quote: string;
  attribution?: string;
  palette?: Palette;
  text_motion?: TextMotionMode;
  accent_fx?: AccentFxMode;
}

export const PullQuote: React.FC<PullQuoteProps> = ({
  quote,
  attribution,
  palette = PALETTES.editorial_dark,
  text_motion = "fade",
  accent_fx = "none",
}) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  const quoteSize = width >= 1280 ? FONT_SIZE[7] : FONT_SIZE[6];
  const attrOpacity = interpolate(frame, [fps * 0.6, fps * 1.0], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const quoteStyle: React.CSSProperties = {
    margin: 0,
    fontFamily: FONT_STACK.display,
    fontStyle: "italic",
    fontSize: quoteSize,
    fontWeight: FONT_WEIGHT[4],
    color: palette.text,
    lineHeight: LINE_HEIGHT[2],
    letterSpacing: LETTER_SPACING[1],
    textShadow: `0 1px 12px ${palette.bg}aa`,
  };

  const isCharMode = text_motion === "typewriter" || text_motion === "wave";
  const quoteEl = isCharMode ? (
    <blockquote style={quoteStyle}><TextMotion mode={text_motion} text={quote} /></blockquote>
  ) : (
    <TextMotion mode={text_motion}><blockquote style={quoteStyle}>{quote}</blockquote></TextMotion>
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
          gap: SIZE[5],
        }}
      >
        {/* 大引号：贴着左边，但比标题缩进一点 */}
        <div
          style={{
            fontFamily: FONT_STACK.display,
            fontSize: quoteSize * 2.5,
            color: palette.accent,
            opacity: 0.18,
            lineHeight: LINE_HEIGHT[0],
            fontStyle: "italic",
            marginBottom: -quoteSize,  // 让引号视觉上压在 quote 上方
            marginLeft: -SIZE[3],
          }}
        >
          “
        </div>
        <AccentFx mode={accent_fx} palette={palette}>{quoteEl}</AccentFx>
        {attribution && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: SIZE[3],
              opacity: attrOpacity,
              marginTop: SIZE[3],
            }}
          >
            <div style={{ width: SIZE[6], height: 1, background: palette.textSecondary }} />
            <p
              style={{
                margin: 0,
                fontFamily: FONT_STACK.body,
                fontSize: FONT_SIZE[2],
                color: palette.textSecondary,
                letterSpacing: LETTER_SPACING[4],
                textTransform: "uppercase",
              }}
            >
              {attribution}
            </p>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
