import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { AccentFx, type AccentFxMode } from "../motion/AccentFx";
import { TextMotion, type TextMotionMode } from "../motion/TextMotion";
import { FONTS, PALETTES, type Palette } from "../theme";

export interface TitleCardProps {
  title: string;
  subtitle?: string;
  /** Optional eyebrow line above the title (e.g. "Chapter 03"). */
  eyebrow?: string;
  palette?: Palette;
  text_motion?: TextMotionMode;
  accent_fx?: AccentFxMode;
}

export const TitleCard: React.FC<TitleCardProps> = ({
  title,
  subtitle,
  eyebrow,
  palette = PALETTES.editorial_dark,
  text_motion = "fade",
  accent_fx = "none",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Subtle rule line that draws in left-to-right; only shown when accent_fx
  // does not already supply a decoration (avoid double-line).
  const ruleProgress = interpolate(frame, [fps * 0.3, fps * 1.2], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const showRule = accent_fx === "none" || accent_fx === "glow";

  const titleStyle: React.CSSProperties = {
    margin: 0,
    fontFamily: FONTS.display,
    fontWeight: 400,
    fontSize: "clamp(48px, 7vw, 116px)",
    color: palette.text,
    textAlign: "center",
    lineHeight: 1.1,
  };

  const isCharMode = text_motion === "typewriter" || text_motion === "wave";
  const titleEl = isCharMode ? (
    <h1 style={titleStyle}>
      <TextMotion mode={text_motion} text={title} />
    </h1>
  ) : (
    <TextMotion mode={text_motion}>
      <h1 style={titleStyle}>{title}</h1>
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
          padding: "0 8%",
        }}
      >
        {eyebrow && (
          <TextMotion mode="fade" durationFrames={Math.round(fps * 0.4)}>
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
          </TextMotion>
        )}
        <AccentFx mode={accent_fx} palette={palette} startFrame={0}>
          {titleEl}
        </AccentFx>
        {showRule && (
          <div
            style={{
              marginTop: 28,
              width: `${ruleProgress * 18}%`,
              height: 1,
              background: palette.textSecondary,
              transformOrigin: "left",
            }}
          />
        )}
        {subtitle && (
          <TextMotion mode="fade" startFrame={Math.round(fps * 0.4)}>
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
          </TextMotion>
        )}
      </div>
    </AbsoluteFill>
  );
};
