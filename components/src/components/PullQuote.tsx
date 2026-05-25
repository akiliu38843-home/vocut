import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS, FONTS } from "../theme";

export interface PullQuoteProps {
  quote: string;
  attribution?: string;
}

export const PullQuote: React.FC<PullQuoteProps> = ({ quote, attribution }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const quoteOpacity = interpolate(frame, [0, fps * 0.6], [0, 1], { extrapolateRight: "clamp" });
  const quoteShift = interpolate(frame, [0, fps * 0.6], [16, 0], { extrapolateRight: "clamp" });
  const attrOpacity = interpolate(frame, [fps * 0.6, fps * 1.0], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: COLORS.bg.pullQuote }}>
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
        {/* Oversized opening quote mark, sits behind the text */}
        <div
          style={{
            position: "absolute",
            top: "12%",
            left: "10%",
            fontFamily: FONTS.display,
            fontSize: 280,
            color: COLORS.text.accent,
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
            color: COLORS.text.primary,
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
              color: COLORS.text.secondary,
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
