// DynamicHighlight: KeywordHighlight 的"动态版" — 逐字揭示 + 关键词描边下划线
//
// 套路: #2 Sequential Word Reveal (入场) + #6 Trim Path Underline 简化版 (highlight 强调)
// 与老 KeywordHighlight 同 props 接口.

import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { SequentialWord } from "../patterns";
import { PALETTES, type Palette } from "../theme";
import {
  FONT_STACK, FONT_WEIGHT,
  LETTER_SPACING, LINE_HEIGHT, SIZE, TYPE_RATIO,
  MOTION_STAGGER, MOTION_DURATION,
} from "../tokens";

export interface DynamicHighlightProps {
  text: string;
  highlight?: string;
  palette?: Palette;
  staggerMs?: number;
}

const hasChinese = (s: string): boolean => /[一-龥]/.test(s);

export const DynamicHighlight: React.FC<DynamicHighlightProps> = ({
  text,
  highlight,
  palette = PALETTES.editorial_dark,
  staggerMs,
}) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const textSize = Math.round(height * TYPE_RATIO.primary);

  const mode = hasChinese(text) ? "char" : "word";
  const effectiveStagger =
    staggerMs ?? (mode === "char" ? MOTION_STAGGER.tight : MOTION_STAGGER.normal);

  // 把 text 按 highlight 切 3 段 (前 / 高亮 / 后)
  let before = text;
  let middle = "";
  let after = "";
  if (highlight && text.includes(highlight)) {
    const idx = text.indexOf(highlight);
    before = text.slice(0, idx);
    middle = highlight;
    after = text.slice(idx + highlight.length);
  }

  // 计算每段什么时候开始
  const beforeSegCount = mode === "char" ? Array.from(before).length : before.split(/\s+/).filter(Boolean).length;
  const middleSegCount = mode === "char" ? Array.from(middle).length : middle.split(/\s+/).filter(Boolean).length;
  const middleStartFrame = (beforeSegCount * effectiveStagger / 1000) * fps;
  const afterStartFrame = ((beforeSegCount + middleSegCount) * effectiveStagger / 1000) * fps;

  // 关键词下划线: 在 middle 出完后 + 200ms 延迟才画
  const underlineStartFrame = afterStartFrame + (MOTION_DURATION.fast / 1000) * fps;
  const underlineEndFrame = underlineStartFrame + (MOTION_DURATION.slow / 1000) * fps;
  const underlineProgress = interpolate(
    frame,
    [underlineStartFrame, underlineEndFrame],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: (t) => t < 0.5 ? 2*t*t : 1 - Math.pow(-2*t+2, 2)/2 },
  );

  const baseStyle: React.CSSProperties = {
    margin: 0,
    fontFamily: FONT_STACK.body,
    fontSize: textSize,
    fontWeight: FONT_WEIGHT[5],
    color: palette.text,
    lineHeight: LINE_HEIGHT[2],
    letterSpacing: LETTER_SPACING[2],
  };

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
        }}
      >
        <p style={baseStyle}>
          {before && <SequentialWord text={before} mode={mode} staggerMs={effectiveStagger} startFrame={0} />}
          {middle && (
            <span
              style={{
                position: "relative",
                color: palette.accent,
                fontWeight: FONT_WEIGHT[7],
                marginLeft: before ? "0.2em" : 0,
                marginRight: after ? "0.2em" : 0,
              }}
            >
              <SequentialWord text={middle} mode={mode} staggerMs={effectiveStagger} startFrame={middleStartFrame} />
              {/* 描边下划线 */}
              <span
                style={{
                  position: "absolute",
                  left: 0,
                  bottom: "-0.05em",
                  height: "0.08em",
                  width: `${underlineProgress * 100}%`,
                  background: palette.accent,
                  transformOrigin: "left",
                }}
              />
            </span>
          )}
          {after && <SequentialWord text={after} mode={mode} staggerMs={effectiveStagger} startFrame={afterStartFrame} />}
        </p>
      </div>
    </AbsoluteFill>
  );
};
