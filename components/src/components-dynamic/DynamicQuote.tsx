// DynamicQuote: PullQuote 的"动态版" — 逐字逐词揭示 (套路 #2 Sequential Word Reveal)
//
// 与老 PullQuote 同 props 接口.
// 中文按字 stagger 80ms (CMU 推荐下限), 英文按词 120ms.

import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { SequentialWord } from "../patterns";
import { PALETTES, type Palette } from "../theme";
import {
  FONT_STACK, FONT_WEIGHT,
  LETTER_SPACING, LINE_HEIGHT, SIZE, TYPE_RATIO,
  MOTION_STAGGER, MOTION_DURATION,
} from "../tokens";

export interface DynamicQuoteProps {
  quote: string;
  attribution?: string;
  palette?: Palette;
  staggerMs?: number;
}

const hasChinese = (s: string): boolean => /[一-龥]/.test(s);

export const DynamicQuote: React.FC<DynamicQuoteProps> = ({
  quote,
  attribution,
  palette = PALETTES.editorial_dark,
  staggerMs,
}) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const quoteSize = Math.round(height * TYPE_RATIO.primary);
  const attrSize = Math.round(height * TYPE_RATIO.label);

  const mode = hasChinese(quote) ? "char" : "word";
  const effectiveStagger =
    staggerMs ?? (mode === "char" ? MOTION_STAGGER.tight : MOTION_STAGGER.normal);

  // 估算引言总长 (stagger × 字数) + buffer, 之后 attribution 入场
  const segCount = mode === "char" ? Array.from(quote).length : quote.split(/\s+/).length;
  const quoteEndFrame = (segCount * effectiveStagger + MOTION_DURATION.fast) / 1000 * fps;
  const attrStart = quoteEndFrame + (MOTION_DURATION.instant / 1000) * fps;
  const attrEnd = attrStart + (MOTION_DURATION.fast / 1000) * fps;
  const attrOpacity = interpolate(frame, [attrStart, attrEnd], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ background: palette.bg }}>
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
        <blockquote
          style={{
            margin: 0,
            fontFamily: FONT_STACK.display,
            fontStyle: "italic",
            fontSize: quoteSize,
            fontWeight: FONT_WEIGHT[4],
            color: palette.text,
            lineHeight: LINE_HEIGHT[2],
            letterSpacing: LETTER_SPACING[1],
            textShadow: `0 1px 12px ${palette.bg}aa`,
          }}
        >
          <SequentialWord text={quote} mode={mode} staggerMs={effectiveStagger} />
        </blockquote>
        {attribution && (
          <div
            style={{
              opacity: attrOpacity,
              fontFamily: FONT_STACK.mono,
              fontSize: attrSize,
              fontWeight: FONT_WEIGHT[5],
              color: palette.textSecondary,
              letterSpacing: LETTER_SPACING[6],
              textTransform: "uppercase",
            }}
          >
            — {attribution}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
