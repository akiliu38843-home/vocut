// Pattern #3: Spotlight Cycle (聚光循环高亮)
//
// 来源: Material Design 3 "focused" 原则 + NN/G "guide attention"
//   - 屏上一段话全部在场, 旁白读到哪句, 那句高亮 (其他变灰 opacity 0.35)
//   - 切换时长 200-300ms (UI 标准), 视频 × 1.5 ≈ MOTION_DURATION.fast = 300ms
// 给 DynamicHighlight 用.
//
// 约束: 同时只能 1 个主焦点. 如果要 highlight 2 句以上, 是错的 (主焦点不能拆).

import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { MOTION_DURATION, MOTION_EASE } from "../tokens";

type SpotlightSegment = {
  /** 显示的文字 */
  text: string;
  /** 这段什么时候开始高亮 (秒, 相对场景起点) */
  startSec: number;
  /** 这段什么时候不再高亮 (秒). 不给就一直亮到下段开始. */
  endSec?: number;
};

type SpotlightCycleProps = {
  segments: SpotlightSegment[];
  /** 非高亮态透明度. NN/G 默认 0.35 */
  dimmedOpacity?: number;
  /** 切换时长 ms */
  switchDurationMs?: number;
};

/**
 * 给一组段落 + 每段的 startSec, 渲染"读到哪句亮哪句".
 *
 * 输入示例:
 *   segments: [
 *     { text: "AI 不会停下来", startSec: 0.0 },
 *     { text: "但人会被甩在后面", startSec: 1.8 },
 *   ]
 */
export const SpotlightCycle: React.FC<SpotlightCycleProps> = ({
  segments,
  dimmedOpacity = 0.35,
  switchDurationMs = MOTION_DURATION.fast,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const switchFrames = (switchDurationMs / 1000) * fps;

  // 找出当前激活的段 (最后一个 startSec ≤ currentSec 的段)
  const currentSec = frame / fps;
  let activeIdx = -1;
  segments.forEach((seg, i) => {
    if (seg.startSec <= currentSec) activeIdx = i;
  });

  return (
    <>
      {segments.map((seg, i) => {
        const startFrame = seg.startSec * fps;
        // i=activeIdx 是亮的, 其他段是暗的
        const targetOpacity = i === activeIdx ? 1 : dimmedOpacity;
        // 平滑过渡: 在 startFrame 之后过渡 switchFrames 帧才到目标
        const opacity = interpolate(
          frame,
          [startFrame, startFrame + switchFrames],
          [dimmedOpacity, targetOpacity],
          {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: (t) => {
              // Material standard ease-in-out 近似
              return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
            },
          }
        );

        // 没轮到的段一直保持 dimmed
        const finalOpacity = currentSec < seg.startSec ? dimmedOpacity : opacity;

        return (
          <div
            key={i}
            style={{
              opacity: finalOpacity,
              transition: "none", // Remotion 控制, 不要 CSS transition 干扰
              willChange: "opacity",
            }}
          >
            {seg.text}
          </div>
        );
      })}
    </>
  );
};
