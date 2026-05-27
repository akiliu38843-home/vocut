/**
 * SceneFrame — 给每张卡加 minimal "纪录片"质感:
 *   - 左上角监督文字（mono 字体）：仅一行 "01 / 16 — SECTION_NAME"
 *   - 不再画任何 hairline 浮空横线 / 角标 / 斜切线（之前那是噪声）
 *
 * 真正的 hierarchy 由组件内部用 tokens.ts 的字号/空白阶梯建立，
 * SceneFrame 只负责"画面有一行编号"，不负责画框。
 */

import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import type { Palette } from "./theme";
import { FONT_WEIGHT, FONT_STACK, LETTER_SPACING, SIZE, TYPE_RATIO } from "./tokens";

export interface SceneFrameProps {
  palette: Palette;
  style_pack?: "editorial" | "anime" | string;
  scene_idx?: number;
  total_scenes?: number;
  section_label?: string;
  children: React.ReactNode;
}

export const SceneFrame: React.FC<SceneFrameProps> = ({
  palette,
  style_pack: _style_pack,
  scene_idx,
  total_scenes,
  section_label,
  children,
}) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const monitorSize = Math.round(height * TYPE_RATIO.mono);
  const monitorOpacity = interpolate(frame, [fps * 0.2, fps * 0.7], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const sceneNum =
    scene_idx !== undefined && total_scenes !== undefined
      ? `${String(scene_idx + 1).padStart(2, "0")} / ${String(total_scenes).padStart(2, "0")}`
      : null;

  const showMonitor = sceneNum !== null || !!section_label;

  return (
    <>
      {children}
      {showMonitor && (
        <AbsoluteFill
          style={{
            pointerEvents: "none",
            padding: `${SIZE[6]}px ${SIZE[7]}px`,
            opacity: monitorOpacity,
          }}
        >
          <div
            style={{
              fontFamily: FONT_STACK.mono,
              fontSize: monitorSize,
              fontWeight: FONT_WEIGHT[5],
              color: palette.textSecondary,
              letterSpacing: LETTER_SPACING[6],
              textTransform: "uppercase",
              whiteSpace: "nowrap",
              opacity: 0.7,
            }}
          >
            {sceneNum}
            {sceneNum && section_label ? "  ·  " : ""}
            {section_label}
          </div>
        </AbsoluteFill>
      )}
    </>
  );
};
