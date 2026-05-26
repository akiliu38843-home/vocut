import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { AccentFx, type AccentFxMode } from "../motion/AccentFx";
import { TextMotion, type TextMotionMode } from "../motion/TextMotion";
import { FONTS, PALETTES, type Palette } from "../theme";

export interface KeyNumberProps {
  /** The big number, exactly as text. */
  primary: string;
  unit?: string;
  label?: string;
  secondary?: string;
  palette?: Palette;
  text_motion?: TextMotionMode;
  accent_fx?: AccentFxMode;
}

export const KeyNumber: React.FC<KeyNumberProps> = ({
  primary,
  unit,
  label,
  secondary,
  palette = PALETTES.editorial_dark,
  text_motion = "scale_in",
  accent_fx = "none",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Stagger unit + label entries (kept from Phase A behavior).
  const unitOpacity = interpolate(frame, [fps * 0.4, fps * 0.7], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const labelOpacity = interpolate(frame, [fps * 0.7, fps * 1.0], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const primaryStyle: React.CSSProperties = {
    fontFamily: FONTS.display,
    fontSize: "clamp(140px, 18vw, 280px)",
    fontWeight: 500,
    color: palette.accent,
    lineHeight: 1,
    letterSpacing: -2,
  };

  const isCharMode = text_motion === "typewriter" || text_motion === "wave";
  const primaryEl = isCharMode ? (
    <span style={primaryStyle}>
      <TextMotion mode={text_motion} text={primary} />
    </span>
  ) : (
    <TextMotion mode={text_motion}>
      <span style={primaryStyle}>{primary}</span>
    </TextMotion>
  );

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
        <div style={{ display: "flex", alignItems: "baseline", gap: 24 }}>
          <AccentFx mode={accent_fx} palette={palette}>
            {primaryEl}
          </AccentFx>
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
