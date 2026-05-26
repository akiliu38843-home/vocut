import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { AccentFx, type AccentFxMode } from "../motion/AccentFx";
import { TextMotion, type TextMotionMode } from "../motion/TextMotion";
import { FONTS, PALETTES, type Palette } from "../theme";

export interface PullQuoteProps {
  quote: string;
  attribution?: string;
  palette?: Palette;
  text_motion?: TextMotionMode;
  accent_fx?: AccentFxMode;
}

export const PullQuote: React.FC<PullQuoteProps> = ({
  quote,
  attribution,
  palette = PALETTES.editorial_dark,
  text_motion = "fade",
  accent_fx = "none",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const attrOpacity = interpolate(frame, [fps * 0.6, fps * 1.0], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const quoteStyle: React.CSSProperties = {
    margin: 0,
    fontFamily: FONTS.display,
    fontStyle: "italic",
    fontSize: "clamp(40px, 5vw, 78px)",
    color: palette.text,
    textAlign: "center",
    lineHeight: 1.35,
  };

  const isCharMode = text_motion === "typewriter" || text_motion === "wave";
  const quoteEl = isCharMode ? (
    <blockquote style={quoteStyle}>
      <TextMotion mode={text_motion} text={quote} />
    </blockquote>
  ) : (
    <TextMotion mode={text_motion}>
      <blockquote style={quoteStyle}>{quote}</blockquote>
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
          padding: "0 12%",
        }}
      >
        {/* Oversized opening quote mark sits behind the text */}
        <div
          style={{
            position: "absolute",
            top: "12%",
            left: "10%",
            fontFamily: FONTS.display,
            fontSize: 280,
            color: palette.accent,
            opacity: 0.18,
            lineHeight: 1,
            fontStyle: "italic",
          }}
        >
          “
        </div>
        <AccentFx mode={accent_fx} palette={palette}>
          {quoteEl}
        </AccentFx>
        {attribution && (
          <p
            style={{
              marginTop: 40,
              fontFamily: FONTS.body,
              fontSize: 26,
              color: palette.textSecondary,
              letterSpacing: 1,
              opacity: attrOpacity,
            }}
          >
            — {attribution}
          </p>
        )}
      </div>
    </AbsoluteFill>
  );
};
