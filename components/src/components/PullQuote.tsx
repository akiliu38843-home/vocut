import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { FONTS, PALETTES, type Palette } from "../theme";

export interface PullQuoteProps {
  quote: string;
  attribution?: string;
  palette?: Palette;
  text_motion?: string;
  accent_fx?: string;
}

export const PullQuote: React.FC<PullQuoteProps> = ({
  quote,
  attribution,
  palette = PALETTES.editorial_dark,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const quoteOpacity = interpolate(frame, [0, fps * 0.6], [0, 1], { extrapolateRight: "clamp" });
  const quoteShift = interpolate(frame, [0, fps * 0.6], [16, 0], { extrapolateRight: "clamp" });
  const attrOpacity = interpolate(frame, [fps * 0.6, fps * 1.0], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

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
        <blockquote
          style={{
            margin: 0,
            fontFamily: FONTS.display,
            fontStyle: "italic",
            fontSize: "clamp(40px, 5vw, 78px)",
            color: palette.text,
            textAlign: "center",
            lineHeight: 1.35,
            opacity: quoteOpacity,
            transform: `translateY(${quoteShift}px)`,
          }}
        >
          {quote}
        </blockquote>
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
