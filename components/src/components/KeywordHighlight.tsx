import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { AccentFx, type AccentFxMode } from "../motion/AccentFx";
import { TextMotion, type TextMotionMode } from "../motion/TextMotion";
import { FONTS, PALETTES, type Palette } from "../theme";

export interface KeywordHighlightProps {
  /** Full sentence. */
  text: string;
  /** Substring of `text` to emphasize. */
  highlight?: string;
  palette?: Palette;
  text_motion?: TextMotionMode;
  accent_fx?: AccentFxMode;
}

export const KeywordHighlight: React.FC<KeywordHighlightProps> = ({
  text,
  highlight,
  palette = PALETTES.editorial_dark,
  text_motion = "fade",
  accent_fx = "none",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Highlight reveal delay (kept from Phase A behavior).
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

  // Char-based motion modes can't show a partial-string highlight color, so
  // they render the whole text flat in palette.text.
  const isCharMode = text_motion === "typewriter" || text_motion === "wave";

  const textBlock = isCharMode ? (
    <TextMotion mode={text_motion} text={text} />
  ) : (
    <TextMotion mode={text_motion}>
      <span>
        {before}
        {middle && (
          <AccentFx mode={accent_fx} palette={palette} startFrame={Math.round(fps * 0.5)}>
            <span style={{ color: palette.accent, opacity: highlightOpacity }}>{middle}</span>
          </AccentFx>
        )}
        {after}
      </span>
    </TextMotion>
  );

  return (
    <AbsoluteFill>
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
          color: palette.text,
          lineHeight: 1.3,
          textAlign: "center",
        }}
      >
        <div>{textBlock}</div>
      </div>
    </AbsoluteFill>
  );
};
