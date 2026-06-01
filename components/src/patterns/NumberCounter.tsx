// Pattern #4: Number Counter / Tick-Up (数字滚动)
//
// 来源: UX 标准 (Material "informative" 原则) + Vox 经典招
//   - 总滚动时长 800-1200ms (跟数字大小, < 1k → 800ms, > 10k → 1200ms)
//   - ease-out cubic (开始快, 结束慢)
//   - 单位在数字滚完后 +100ms 入场 (避免拥挤)
// 给 DynamicNumber 用.
//
// 反则: 不要 > 1.5s. 单位别跟数字同时进场.

import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { MOTION_DURATION } from "../tokens";

type NumberCounterProps = {
  /** 终值 */
  to: number;
  /** 起值 (默认 0) */
  from?: number;
  /** 总滚动时长 ms. 不给的话按数字量级估: <1k→800, <10k→1000, >10k→1200 */
  durationMs?: number;
  /** 小数位 */
  decimals?: number;
  /** 千分位分隔 */
  withSeparator?: boolean;
  /** 起始帧 (相对当前 sequence) */
  startFrame?: number;
};

const pickDuration = (to: number): number => {
  const abs = Math.abs(to);
  if (abs < 1_000) return 800;
  if (abs < 10_000) return MOTION_DURATION.transition - 200; // 1000
  return MOTION_DURATION.transition; // 1200
};

/**
 * 滚动数字, 用 Remotion frame 精准对齐时间轴.
 */
export const NumberCounter: React.FC<NumberCounterProps> = ({
  to,
  from = 0,
  durationMs,
  decimals = 0,
  withSeparator = false,
  startFrame = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const effectiveDuration = durationMs ?? pickDuration(to);
  const totalFrames = (effectiveDuration / 1000) * fps;

  const progress = interpolate(
    frame,
    [startFrame, startFrame + totalFrames],
    [0, 1],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: (t) => 1 - Math.pow(1 - t, 3), // ease-out cubic
    }
  );

  const value = from + (to - from) * progress;
  const fixed = value.toFixed(decimals);
  const display = withSeparator
    ? Number(fixed).toLocaleString("en-US", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      })
    : fixed;

  // 等宽数字让滚动时位数不抖
  return <span style={{ fontVariantNumeric: "tabular-nums" }}>{display}</span>;
};
