import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { FONTS, PALETTES, type Palette } from "../theme";

export interface KeyNumberProps {
  /** The big number, exactly as text (e.g. "4000 万", "60", "$4.2 亿"). */
  primary: string;
  /** Optional unit suffix (e.g. "美元", "%", "年"). */
  unit?: string;
  /** Optional caption below (e.g. "Sensor Tower Q1 2026"). */
  label?: string;
  /** Optional secondary metric (e.g. "海外占 38%"). */
  secondary?: string;
  palette?: Palette;
  text_motion?: string;
  accent_fx?: string;
}

export const KeyNumber: React.FC<KeyNumberProps> = ({
  primary,
  unit,
  label,
  secondary,
  palette = PALETTES.editorial_dark,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({ frame, fps, config: { damping: 18, stiffness: 110 } });
  const baseOpacity = interpolate(frame, [0, fps * 0.4], [0, 1], { extrapolateRight: "clamp" });
  const unitOpacity = interpolate(frame, [fps * 0.4, fps * 0.7], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const labelOpacity = interpolate(frame, [fps * 0.7, fps * 1.0], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          height: "100%",
          width: "100%",
          alignItems: "center",
          justifyContent: "center",
          padding: "0 6%",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "baseline",
            gap: 24,
            transform: `scale(${0.92 + scale * 0.08})`,
            opacity: baseOpacity,
          }}
        >
          <span
            style={{
              fontFamily: FONTS.display,
              fontSize: "clamp(140px, 18vw, 280px)",
              fontWeight: 500,
              color: palette.accent,
              lineHeight: 1,
              letterSpacing: -2,
            }}
          >
            {primary}
          </span>
          {unit && (
            <span
              style={{
                fontFamily: FONTS.body,
                fontSize: "clamp(40px, 5vw, 80px)",
                color: palette.text,
                opacity: unitOpacity,
                fontWeight: 300,
              }}
            >
              {unit}
            </span>
          )}
        </div>
        {label && (
          <p
            style={{
              marginTop: 32,
              fontFamily: FONTS.body,
              fontSize: 32,
              color: palette.textSecondary,
              textAlign: "center",
              opacity: labelOpacity,
            }}
          >
            {label}
          </p>
        )}
        {secondary && (
          <p
            style={{
              marginTop: 8,
              fontFamily: FONTS.mono,
              fontSize: 22,
              color: palette.quiet,
              textAlign: "center",
              opacity: labelOpacity,
            }}
          >
            {secondary}
          </p>
        )}
      </div>
    </AbsoluteFill>
  );
};
