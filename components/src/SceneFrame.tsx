/**
 * SceneFrame — the consistent "framing" layer wrapped around every
 * dispatched card. Adds:
 *   - monospace monitor text at top-left: "01 / 16 — SECTION_NAME"
 *   - top + bottom 1px rules (editorial pack) or diagonal corner slashes
 *     (anime pack) for "画面框感"
 *   - safe-area padding so content never touches the AbsoluteFill edge
 *
 * The frame ITSELF takes very little visual weight — its only job is to
 * give the otherwise-empty background a sense of intentional density.
 */

import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import type { Palette } from "./theme";
import { FONTS } from "./theme";

export interface SceneFrameProps {
  palette: Palette;
  /** "editorial" or "anime" — controls the decoration line style. */
  style_pack?: "editorial" | "anime" | string;
  scene_idx?: number;
  total_scenes?: number;
  section_label?: string;
  /** Children are the actual card body. */
  children: React.ReactNode;
}

export const SceneFrame: React.FC<SceneFrameProps> = ({
  palette,
  style_pack = "editorial",
  scene_idx,
  total_scenes,
  section_label,
  children,
}) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();

  // Frame elements fade in slightly slower than content so the body lands first.
  const frameOpacity = interpolate(frame, [0, fps * 0.5], [0, 1], {
    extrapolateRight: "clamp",
  });
  const ruleProgress = interpolate(frame, [fps * 0.3, fps * 1.1], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const monitor =
    scene_idx !== undefined && total_scenes !== undefined
      ? `${String(scene_idx + 1).padStart(2, "0")} / ${String(total_scenes).padStart(2, "0")}` +
        (section_label ? `  —  ${section_label}` : "")
      : section_label || "";

  // Frame edge padding: percentages so vertical/landscape both look right.
  const padX = "5%";
  const padY = "4%";

  const isAnime = style_pack === "anime";

  return (
    <>
      {children}

      {/* Monitor / supervisory text — top-left */}
      {monitor && (
        <AbsoluteFill
          style={{
            pointerEvents: "none",
            padding: `${padY} ${padX}`,
            opacity: frameOpacity,
          }}
        >
          <div
            style={{
              fontFamily: FONTS.mono,
              fontSize: Math.max(11, Math.round(height / 80)),
              color: palette.textSecondary,
              letterSpacing: 2,
              textTransform: "uppercase",
              whiteSpace: "nowrap",
            }}
          >
            {monitor}
          </div>
        </AbsoluteFill>
      )}

      {/* Top & bottom hairlines */}
      <AbsoluteFill
        style={{
          pointerEvents: "none",
          padding: `${padY} ${padX}`,
          opacity: frameOpacity,
        }}
      >
        <div
          style={{
            position: "absolute",
            top: padY,
            left: padX,
            right: padX,
            transform: `scaleX(${ruleProgress})`,
            transformOrigin: "left",
          }}
        >
          <div style={{ height: 1, background: palette.textSecondary, opacity: 0.5 }} />
        </div>
        <div
          style={{
            position: "absolute",
            bottom: padY,
            left: padX,
            right: padX,
            transform: `scaleX(${ruleProgress})`,
            transformOrigin: "right",
          }}
        >
          <div style={{ height: 1, background: palette.textSecondary, opacity: 0.5 }} />
        </div>
      </AbsoluteFill>

      {/* Anime corner accents — diagonal slashes top-right + bottom-left */}
      {isAnime && (
        <AbsoluteFill style={{ pointerEvents: "none", opacity: frameOpacity }}>
          <svg
            style={{
              position: "absolute",
              top: padY,
              right: padX,
              width: "10%",
              height: "10%",
            }}
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
          >
            <line x1="100" y1="0" x2="0" y2="100" stroke={palette.accent} strokeWidth="2" strokeDasharray={`${ruleProgress * 140} 200`} />
            <line x1="100" y1="20" x2="20" y2="100" stroke={palette.accent} strokeWidth="2" strokeDasharray={`${ruleProgress * 110} 200`} />
            <line x1="100" y1="40" x2="40" y2="100" stroke={palette.accent} strokeWidth="2" strokeDasharray={`${ruleProgress * 80} 200`} />
          </svg>
          <svg
            style={{
              position: "absolute",
              bottom: padY,
              left: padX,
              width: "10%",
              height: "10%",
            }}
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
          >
            <line x1="0" y1="100" x2="100" y2="0" stroke={palette.accent} strokeWidth="2" strokeDasharray={`${ruleProgress * 140} 200`} />
            <line x1="0" y1="80" x2="80" y2="0" stroke={palette.accent} strokeWidth="2" strokeDasharray={`${ruleProgress * 110} 200`} />
            <line x1="0" y1="60" x2="60" y2="0" stroke={palette.accent} strokeWidth="2" strokeDasharray={`${ruleProgress * 80} 200`} />
          </svg>
        </AbsoluteFill>
      )}

      {/* Corner section label — bottom-right for editorial sense */}
      {!isAnime && total_scenes !== undefined && (
        <AbsoluteFill
          style={{
            pointerEvents: "none",
            padding: `${padY} ${padX}`,
            opacity: frameOpacity,
          }}
        >
          <div
            style={{
              position: "absolute",
              bottom: padY,
              right: padX,
              fontFamily: FONTS.mono,
              fontSize: Math.max(10, Math.round(height / 95)),
              color: palette.quiet,
              letterSpacing: 1,
            }}
          >
            vocut · {String(scene_idx ?? 0 + 1).padStart(2, "0")} / {total_scenes}
          </div>
        </AbsoluteFill>
      )}
    </>
  );
};
