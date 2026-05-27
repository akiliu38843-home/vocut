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
    // Camera-viewfinder corner marks: each of the 4 corners gets a small
    // L-shaped tick that draws in. Restrained, anchored to the content's
    // bounding box, never reads as cheap clipart.
    const progress = interpolate(localFrame, [0, dur], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    const markSize = 14;        // px of each tick arm
    const inset = 6;            // px outset from content
    const corner = (key: string, side: { top?: 0; bottom?: 0; left?: 0; right?: 0 }, rot: number) => (
      <span
        key={key}
        aria-hidden
        style={{
          position: "absolute",
          ...side,
          width: markSize,
          height: markSize,
          opacity: progress * 0.85,
          transform: `rotate(${rot}deg)`,
          transformOrigin: "center",
        }}
      >
        <span style={{ position: "absolute", top: 0, left: 0, width: markSize, height: 2, background: palette.accent }} />
        <span style={{ position: "absolute", top: 0, left: 0, width: 2, height: markSize, background: palette.accent }} />
      </span>
    );
    return (
      <span
        style={{
          position: "relative",
          display: "inline-block",
          paddingTop: inset,
          paddingBottom: inset,
          paddingLeft: inset + 2,
          paddingRight: inset + 2,
          ...style,
        }}
      >
        {corner("tl", { top: 0, left: 0 }, 0)}
        {corner("tr", { top: 0, right: 0 }, 90)}
        {corner("br", { bottom: 0, right: 0 }, 180)}
        {corner("bl", { bottom: 0, left: 0 }, 270)}
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
