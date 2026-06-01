// Pattern #1: Staggered List Reveal (排队进场列表)
//
// 来源: Material Design 3 (stagger 40-120ms) × 视频系数 1.5 → vocut MOTION_STAGGER.normal = 120ms
// 给 DynamicList 用. 子元素一个接一个上升 + 淡入.
//
// 反则: > 5 项不要 stagger (改"分组"), 走 W.7+ 增强.

import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { MOTION_DURATION, MOTION_STAGGER, MOTION_EASE } from "../tokens";

type StaggeredRevealProps = {
  children: React.ReactNode[];
  staggerMs?: number;
  itemDurationMs?: number;
  startFrame?: number;
};

/**
 * 给一组子元素, 按 staggerMs 排队入场.
 * 第 i 个元素的"出场起点" = startFrame + i × staggerFrames.
 */
export const StaggeredReveal: React.FC<StaggeredRevealProps> = ({
  children,
  staggerMs = MOTION_STAGGER.normal,
  itemDurationMs = MOTION_DURATION.base,
  startFrame = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const staggerFrames = (staggerMs / 1000) * fps;
  const itemFrames = (itemDurationMs / 1000) * fps;

  return (
    <>
      {React.Children.map(children, (child, i) => {
        const itemStart = startFrame + i * staggerFrames;
        const progress = interpolate(
          frame,
          [itemStart, itemStart + itemFrames],
          [0, 1],
          {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: (t) => {
              // Material standard cubic-bezier(0.2, 0, 0, 1) 近似
              const [, , , p3] = MOTION_EASE.standard;
              return 1 - Math.pow(1 - t, 3); // ease-out cubic
            },
          }
        );

        return (
          <div
            style={{
              opacity: progress,
              transform: `translateY(${(1 - progress) * 20}px)`,
              willChange: "opacity, transform",
            }}
          >
            {child}
          </div>
        );
      })}
    </>
  );
};
