import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS, FONTS } from "../theme";

export interface KeywordHighlightProps {
  /** Full sentence — the entire thing is shown; the highlighted slice is amber. */
  text: string;
  /** Substring of `text` to emphasize. If absent, no inline highlight. */
  highlight?: string;
}

export const KeywordHighlight: React.FC<KeywordHighlightProps> = ({ text, highlight }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, fps * 0.4], [0, 1], { extrapolateRight: "clamp" });
  const shift = interpolate(frame, [0, fps * 0.4], [8, 0], { extrapolateRight: "clamp" });
  const highlightOpacity = interpolate(
    frame,
    [fps * 0.5, fps * 0.9],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  let before = text;
  let middle = "";
  let after = "";
  if (highlight && text.includes(highlight)) {
    const idx = text.indexOf(highlight);
    before = text.slice(0, idx);
    middle = highlight;
    after = text.slice(idx + highlight.length);
  }

  return (
    <AbsoluteFill style={{ background: COLORS.bg.keywordHighlight }}>
      <div
        style={{
          display: "flex",
          height: "100%",
          width: "100%",
          alignItems: "center",
          justifyContent: "center",
          padding: "0 10%",
          fontFamily: FONTS.body,
          fontSize: "clamp(40px, 5.5vw, 72px)",
          color: COLORS.text.primary,
          lineHeight: 1.3,
          textAlign: "center",
          opacity: fadeIn,
          transform: `translateY(${shift}px)`,
        }}
      >
        <div>
          {before}
          {middle && (
            <span
              style={{
                color: COLORS.text.accent,
                opacity: highlightOpacity,
              }}
            >
              {middle}
            </span>
          )}
          {after}
        </div>
      </div>
    </AbsoluteFill>
  );
};
