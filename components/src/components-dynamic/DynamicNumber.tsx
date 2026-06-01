// DynamicNumber: KeyNumber 的"动态版" — 主数字滚动 + 单位 / 标签分阶段入场
//
// 套路 #4 Number Counter (主数字滚动 800-1200ms ease-out)
// 与老 KeyNumber 同 props 接口.
//
// primary 解析:
//   - 纯数字 ("60", "1234"): 用 NumberCounter 滚动
//   - 含数字 + 文本 ("60亿日元"): 拆"60" + "亿日元", 数字滚动, 文本紧随其后入场
//   - 全文本 ("Q4 2026"): 不滚, 直接淡入

import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { NumberCounter } from "../patterns";
import { PALETTES, type Palette } from "../theme";
import {
  FONT_STACK, FONT_WEIGHT,
  LETTER_SPACING, LINE_HEIGHT, SIZE, TYPE_RATIO,
  MOTION_DURATION,
} from "../tokens";

export interface DynamicNumberProps {
  primary: string;
  unit?: string;
  label?: string;
  secondary?: string;
  palette?: Palette;
  /** 主滚动时长 ms (覆盖 NumberCounter 默认估算) */
  durationMs?: number;
}

/** 把 "60亿日元" 切成 ["60", "亿日元"]. 找开头的数字串 (含小数). */
const splitNumeric = (s: string): { num: number | null; rest: string } => {
  const m = s.trim().match(/^(-?\d{1,3}(?:,\d{3})*(?:\.\d+)?|-?\d+(?:\.\d+)?)(.*)$/);
  if (!m) return { num: null, rest: s };
  const numStr = m[1].replace(/,/g, "");
  const num = Number(numStr);
  if (isNaN(num)) return { num: null, rest: s };
  return { num, rest: m[2] };
};

export const DynamicNumber: React.FC<DynamicNumberProps> = ({
  primary,
  unit,
  label,
  secondary,
  palette = PALETTES.editorial_dark,
  durationMs,
}) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const primarySize = Math.round(height * TYPE_RATIO.giant);
  const labelSize = Math.round(height * TYPE_RATIO.label);
  const secondarySize = Math.round(height * TYPE_RATIO.body);

  const { num, rest: trailing } = splitNumeric(primary);
  const decimals = (() => {
    if (num == null) return 0;
    const m = primary.match(/\.(\d+)/);
    return m ? m[1].length : 0;
  })();

  // unit 去重: 如果 primary 已含 unit, 不要再追加
  const cleanUnit = unit && primary.trim().endsWith(unit.trim()) ? undefined : unit;

  // 时间线: 数字滚动 0 → durationMs, 然后 trailing/unit/label/secondary 各延后 100ms 入场
  const numberDuration = durationMs ?? (num != null
    ? (Math.abs(num) < 1000 ? 800 : Math.abs(num) < 10000 ? 1000 : 1200)
    : MOTION_DURATION.base);
  const numberEndFrame = (numberDuration / 1000) * fps;
  const trailingStartFrame = numberEndFrame + (MOTION_DURATION.instant / 1000) * fps;
  const unitStartFrame = trailingStartFrame;  // trailing 和 unit 同步出 (它们在物理上紧贴)
  const labelStartFrame = unitStartFrame + (MOTION_DURATION.fast / 1000) * fps;
  const secondaryStartFrame = labelStartFrame + (MOTION_DURATION.instant / 1000) * fps;

  const fadeIn = (start: number, dur = MOTION_DURATION.fast) =>
    interpolate(
      frame,
      [start, start + (dur / 1000) * fps],
      [0, 1],
      { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
    );

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
          gap: SIZE[4],
        }}
      >
        {label && (
          <div
            style={{
              opacity: fadeIn(labelStartFrame),
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
        <div
          style={{
            display: "flex",
            alignItems: "baseline",
            gap: "0.15em",
            fontFamily: FONT_STACK.display,
            fontSize: primarySize,
            fontWeight: FONT_WEIGHT[6],
            color: palette.accent,
            lineHeight: LINE_HEIGHT[0],
            letterSpacing: LETTER_SPACING[0],
            textShadow: `0 2px 24px ${palette.accent}33`,
          }}
        >
          {num != null ? (
            <NumberCounter to={num} decimals={decimals} withSeparator={Math.abs(num) >= 1000} durationMs={numberDuration} />
          ) : (
            <span style={{ opacity: fadeIn(0) }}>{primary}</span>
          )}
          {trailing && (
            <span style={{ opacity: fadeIn(trailingStartFrame) }}>{trailing}</span>
          )}
          {cleanUnit && (
            <span
              style={{
                opacity: fadeIn(unitStartFrame),
                fontSize: "0.5em",
                fontWeight: FONT_WEIGHT[5],
                marginLeft: "0.2em",
              }}
            >
              {cleanUnit}
            </span>
          )}
        </div>
        {secondary && (
          <div
            style={{
              opacity: fadeIn(secondaryStartFrame),
              fontFamily: FONT_STACK.body,
              fontSize: secondarySize,
              fontWeight: FONT_WEIGHT[4],
              color: palette.text,
              lineHeight: LINE_HEIGHT[2],
              letterSpacing: LETTER_SPACING[2],
            }}
          >
            {secondary}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
