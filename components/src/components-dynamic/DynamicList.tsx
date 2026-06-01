// DynamicList: ListItem 的"动态版" — 子项排队进场 (套路 #1 Staggered List Reveal)
//
// 与老 ListItem 同 props 接口, plan.json 不用改.
// 内部用 patterns/StaggeredReveal, 默认 stagger 120ms, item duration 500ms.

import React from "react";
import { AbsoluteFill, useVideoConfig } from "remotion";
import { StaggeredReveal } from "../patterns";
import { PALETTES, type Palette } from "../theme";
import {
  FONT_STACK, FONT_WEIGHT,
  LETTER_SPACING, LINE_HEIGHT, SIZE, TYPE_RATIO,
  MOTION_STAGGER, MOTION_DURATION,
} from "../tokens";

export interface DynamicListProps {
  items: string[];
  label?: string;
  style?: "decimal" | "none";
  palette?: Palette;
  /** 可选: LLM 给具体 stagger ms 覆盖默认 */
  staggerMs?: number;
  /** 可选: 单项入场时长覆盖 */
  itemDurationMs?: number;
}

export const DynamicList: React.FC<DynamicListProps> = ({
  items,
  label,
  style = "decimal",
  palette = PALETTES.editorial_dark,
  staggerMs = MOTION_STAGGER.normal,
  itemDurationMs = MOTION_DURATION.base,
}) => {
  const { height } = useVideoConfig();
  const itemSize = Math.round(height * TYPE_RATIO.value);
  const labelSize = Math.round(height * TYPE_RATIO.label);
  const numeralSize = Math.round(height * TYPE_RATIO.numeral);

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
        {label && (
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
        )}
        <StaggeredReveal staggerMs={staggerMs} itemDurationMs={itemDurationMs}>
          {items.map((item, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "baseline",
                gap: SIZE[4],
                margin: 0,
                padding: 0,
              }}
            >
              {style === "decimal" && (
                <span
                  style={{
                    fontFamily: FONT_STACK.mono,
                    fontSize: numeralSize,
                    fontWeight: FONT_WEIGHT[6],
                    color: palette.accent,
                    lineHeight: LINE_HEIGHT[1],
                  }}
                >
                  {String(i + 1).padStart(2, "0")}
                </span>
              )}
              <span
                style={{
                  fontFamily: FONT_STACK.body,
                  fontSize: itemSize,
                  fontWeight: FONT_WEIGHT[5],
                  color: palette.text,
                  lineHeight: LINE_HEIGHT[2],
                  letterSpacing: LETTER_SPACING[2],
                }}
              >
                {item}
              </span>
            </div>
          ))}
        </StaggeredReveal>
      </div>
    </AbsoluteFill>
  );
};
