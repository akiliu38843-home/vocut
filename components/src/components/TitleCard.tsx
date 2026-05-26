import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { FONTS, PALETTES, type Palette } from "../theme";

export interface TitleCardProps {
  title: string;
  subtitle?: string;
  /** Optional eyebrow line above the title (e.g. "Chapter 03"). */
  eyebrow?: string;
  /** Palette resolved by Card.tsx. Falls back to editorial_dark. */
  palette?: Palette;
  text_motion?: string;
  accent_fx?: string;
}

export const TitleCard: React.FC<TitleCardProps> = ({
  title,
  subtitle,
  eyebrow,
  palette = PALETTES.editorial_dark,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const fadeFrames = fps * 0.6;
  const opacity = interpolate(frame, [0, fadeFrames], [0, 1], {
    extrapolateRight: "clamp",
  });
  const translateY = interpolate(frame, [0, fadeFrames], [12, 0], {
    extrapolateRight: "clamp",
  });

  const ruleProgress = interpolate(frame, [fadeFrames * 0.5, fps * 1.4], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

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
          padding: "0 8%",
          opacity,
          transform: `translateY(${translateY}px)`,
        }}
      >
        {eyebrow && (
          <div
            style={{
              fontFamily: FONTS.body,
              fontSize: 22,
              letterSpacing: 6,
              textTransform: "uppercase",
              color: palette.textSecondary,
              marginBottom: 28,
            }}
          >
            {eyebrow}
          </div>
        )}
        <h1
          style={{
            margin: 0,
            fontFamily: FONTS.display,
            fontWeight: 400,
            fontSize: "clamp(48px, 7vw, 116px)",
            color: palette.text,
            textAlign: "center",
            lineHeight: 1.1,
          }}
        >
          {title}
        </h1>
        <div
          style={{
            marginTop: 28,
            width: `${ruleProgress * 18}%`,
            height: 1,
            background: palette.textSecondary,
            transformOrigin: "left",
          }}
        />
        {subtitle && (
          <p
            style={{
              marginTop: 28,
              fontFamily: FONTS.body,
              fontSize: 26,
              color: palette.textSecondary,
              textAlign: "center",
              maxWidth: "70%",
            }}
          >
            {subtitle}
          </p>
        )}
      </div>
    </AbsoluteFill>
  );
};
