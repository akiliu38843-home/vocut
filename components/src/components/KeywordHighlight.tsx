import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { AccentFx, type AccentFxMode } from "../motion/AccentFx";
import { TextMotion, type TextMotionMode } from "../motion/TextMotion";
import { PALETTES, type Palette } from "../theme";
import {
  FONT_STACK, FONT_WEIGHT,
  LETTER_SPACING, LINE_HEIGHT, SIZE, TYPE_RATIO,
} from "../tokens";

export interface KeywordHighlightProps {
  text: string;
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
  const { fps, height } = useVideoConfig();
  const textSize = Math.round(height * TYPE_RATIO.primary);
  const highlightOpacity = interpolate(frame, [fps * 0.5, fps * 0.9], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  let before = text;
  let middle = "";
  let after = "";
  if (highlight && text.includes(highlight)) {
    const idx = text.indexOf(highlight);
    before = text.slice(0, idx);
    middle = highlight;
    after = text.slice(idx + highlight.length);
  }

  const isCharMode = text_motion === "typewriter" || text_motion === "wave";

  const baseStyle: React.CSSProperties = {
    margin: 0,
    fontFamily: FONT_STACK.body,
    fontSize: textSize,
    fontWeight: FONT_WEIGHT[5],
    color: palette.text,
    lineHeight: LINE_HEIGHT[2],
    letterSpacing: LETTER_SPACING[2],
    textShadow: `0 1px 16px ${palette.bg}aa`,
  };

  const textBlock = isCharMode ? (
    <TextMotion mode={text_motion} text={text} />
  ) : (
    <TextMotion mode={text_motion}>
      <span>
        {before}
        {middle && (
          <AccentFx mode={accent_fx} palette={palette} startFrame={Math.round(fps * 0.5)}>
            <span style={{ color: palette.accent, opacity: highlightOpacity, fontWeight: FONT_WEIGHT[7] }}>
              {middle}
            </span>
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
          flexDirection: "column",
          height: "100%",
          width: "100%",
          alignItems: "flex-start",
          justifyContent: "center",
          padding: `0 ${SIZE[10]}px`,
        }}
      >
        <div style={baseStyle}>{textBlock}</div>
      </div>
    </AbsoluteFill>
  );
};
