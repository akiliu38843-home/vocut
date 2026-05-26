/**
 * AccentFx — decorative emphasis layered around or behind primary content.
 *
 *   none             — passes children through unchanged
 *   glow             — palette.accent text-shadow on children; bigger glow on
 *                      block elements via filter: drop-shadow.
 *   burst            — radiating 6-line "manga emphasis" pattern behind children
 *   underline_sweep  — a 2px line under children, width animated 0 → 100%
 *
 * Wraps arbitrary children. Caller controls layout; AccentFx only adds the
 * decoration layer.
 */

import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import type { Palette } from "../theme";

export type AccentFxMode = "none" | "glow" | "burst" | "underline_sweep";

export interface AccentFxProps {
  mode?: AccentFxMode;
  palette: Palette;
  /** Frame the decoration should start to appear. Default 0. */
  startFrame?: number;
  /** How long the decoration takes to fully appear. Default ~0.6s. */
  durationFrames?: number;
  children: React.ReactNode;
  /** Optional outer style; the wrapper is position:relative so absolute
   * decoration overlays anchor to it. */
  style?: React.CSSProperties;
}

export const AccentFx: React.FC<AccentFxProps> = ({
  mode = "none",
  palette,
  startFrame = 0,
  durationFrames,
  children,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = durationFrames ?? Math.round(fps * 0.6);
  const localFrame = Math.max(0, frame - startFrame);

  if (mode === "none" || !mode) {
    return <span style={style}>{children}</span>;
  }

  if (mode === "glow") {
    const intensity = interpolate(localFrame, [0, dur], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    return (
      <span
        style={{
          textShadow: `0 0 ${20 * intensity}px ${palette.accent}, 0 0 ${40 * intensity}px ${palette.accent}88`,
          filter: `drop-shadow(0 0 ${10 * intensity}px ${palette.accent}66)`,
          ...style,
        }}
      >
        {children}
      </span>
    );
  }

  if (mode === "burst") {
    // 6 radial lines fanning out from the element's center.
    const progress = interpolate(localFrame, [0, dur], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    const lineCount = 6;
    return (
      <span
        style={{
          position: "relative",
          display: "inline-block",
          ...style,
        }}
      >
        <svg
          aria-hidden
          style={{
            position: "absolute",
            left: "50%",
            top: "50%",
            width: 360,
            height: 360,
            transform: "translate(-50%, -50%)",
            pointerEvents: "none",
            opacity: progress * 0.85,
          }}
          viewBox="-100 -100 200 200"
        >
          {Array.from({ length: lineCount }, (_, i) => {
            const angle = (i / lineCount) * Math.PI * 2;
            const innerR = 55;
            const outerR = 55 + 35 * progress;
            const x1 = Math.cos(angle) * innerR;
            const y1 = Math.sin(angle) * innerR;
            const x2 = Math.cos(angle) * outerR;
            const y2 = Math.sin(angle) * outerR;
            return (
              <line
                key={i}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke={palette.accent}
                strokeWidth={2.5}
                strokeLinecap="round"
              />
            );
          })}
        </svg>
        <span style={{ position: "relative", zIndex: 1 }}>{children}</span>
      </span>
    );
  }

  if (mode === "underline_sweep") {
    const width = interpolate(localFrame, [0, dur], [0, 100], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    return (
      <span
        style={{
          position: "relative",
          display: "inline-block",
          paddingBottom: 8,
          ...style,
        }}
      >
        {children}
        <span
          aria-hidden
          style={{
            position: "absolute",
            left: 0,
            bottom: 0,
            width: `${width}%`,
            height: 2,
            background: palette.accent,
            transformOrigin: "left",
          }}
        />
      </span>
    );
  }

  return <span style={style}>{children}</span>;
};
