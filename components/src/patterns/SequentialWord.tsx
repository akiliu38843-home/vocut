// Pattern #2: Sequential Word Reveal (逐字逐词揭示)
//
// 来源: Barbara Brownie 分类 "Sequential reveal" + CMU Kinetic Typography Engine
//   - 中文按字 stagger 80-120ms (按阅读速度)
//   - 英文按词 stagger 100-150ms
// 给 DynamicQuote / DynamicHighlight 用.

import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { MOTION_DURATION, MOTION_STAGGER } from "../tokens";

type SequentialMode = "char" | "word";

type SequentialWordProps = {
  text: string;
  mode?: SequentialMode;
  staggerMs?: number;
  itemDurationMs?: number;
  startFrame?: number;
};

const splitText = (text: string, mode: SequentialMode): string[] =>
  mode === "char" ? Array.from(text) : text.split(/(\s+)/);

/**
 * 把一段文字按 char/word 切, 一项一项浮起来 + 淡入.
 *
 * - char 模式: 中文 / 短句的逐字 (CMU 论文路径)
 * - word 模式: 英文 / 长句的逐词
 */
export const SequentialWord: React.FC<SequentialWordProps> = ({
  text,
  mode = "char",
  staggerMs,
  itemDurationMs = MOTION_DURATION.fast,
  startFrame = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const effectiveStagger =
    staggerMs ?? (mode === "char" ? MOTION_STAGGER.tight : MOTION_STAGGER.normal);
  const staggerFrames = (effectiveStagger / 1000) * fps;
  const itemFrames = (itemDurationMs / 1000) * fps;

  const segments = splitText(text, mode);

  return (
    <>
      {segments.map((seg, i) => {
        const itemStart = startFrame + i * staggerFrames;
        const progress = interpolate(
          frame,
          [itemStart, itemStart + itemFrames],
          [0, 1],
          {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: (t) => 1 - Math.pow(1 - t, 3), // ease-out cubic
          }
        );

        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              whiteSpace: "pre",
              opacity: progress,
              transform: `translateY(${(1 - progress) * 8}px)`,
              willChange: "opacity, transform",
            }}
          >
            {seg}
          </span>
        );
      })}
    </>
  );
};
