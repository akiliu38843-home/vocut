/**
 * LottieCard — Lottie animation as backdrop + caption on top.
 */

import React, { useEffect, useState } from "react";
import {
  AbsoluteFill,
  cancelRender,
  continueRender,
  delayRender,
  staticFile,
  useVideoConfig,
} from "remotion";
import { Lottie, type LottieAnimationData } from "@remotion/lottie";
import { AccentFx, type AccentFxMode } from "../motion/AccentFx";
import { TextMotion, type TextMotionMode } from "../motion/TextMotion";
import { PALETTES, type Palette } from "../theme";
import {
  FONT_STACK, FONT_WEIGHT,
  LETTER_SPACING, LINE_HEIGHT, SIZE, TYPE_RATIO,
} from "../tokens";

export interface LottieCardProps {
  lottie_id?: string;
  lottie_src?: string;
  caption?: string;
  lottie_opacity?: number;
  palette?: Palette;
  text_motion?: TextMotionMode;
  accent_fx?: AccentFxMode;
}

export const LottieCard: React.FC<LottieCardProps> = ({
  lottie_id = "ripple",
  lottie_src,
  caption,
  lottie_opacity = 0.45,
  palette = PALETTES.editorial_dark,
  text_motion = "fade",
  accent_fx = "none",
}) => {
  const { height } = useVideoConfig();
  const captionSize = Math.round(height * TYPE_RATIO.primary);
  const [animationData, setAnimationData] = useState<LottieAnimationData | null>(null);
  const [handle] = useState(() => delayRender(`lottie:${lottie_id}`));

  useEffect(() => {
    const url = lottie_src ?? staticFile(`lottie/${lottie_id}.json`);
    fetch(url)
      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then((data) => { setAnimationData(data); continueRender(handle); })
      .catch((err) => cancelRender(`lottie ${lottie_id}: ${err.message}`));
  }, [lottie_id, lottie_src, handle]);

  if (!animationData) return <AbsoluteFill style={{ background: palette.bg }} />;

  const isCharMode = text_motion === "typewriter" || text_motion === "wave";
  const captionStyle: React.CSSProperties = {
    margin: 0,
    fontFamily: FONT_STACK.display,
    fontWeight: FONT_WEIGHT[6],
    fontSize: captionSize,
    color: palette.text,
    lineHeight: LINE_HEIGHT[2],
    letterSpacing: LETTER_SPACING[1],
    textShadow: `0 2px 24px ${palette.bg}, 0 0 40px ${palette.bg}aa`,
  };
  const captionEl = caption
    ? isCharMode
      ? <h1 style={captionStyle}><TextMotion mode={text_motion} text={caption} /></h1>
      : <TextMotion mode={text_motion}><h1 style={captionStyle}>{caption}</h1></TextMotion>
    : null;

  return (
    <AbsoluteFill style={{ background: palette.bg }}>
      <AbsoluteFill style={{ opacity: lottie_opacity }}>
        <Lottie animationData={animationData} loop />
      </AbsoluteFill>
      {captionEl && (
        <AbsoluteFill
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "flex-start",
            padding: `0 ${SIZE[10]}px`,
            zIndex: 2,
          }}
        >
          <AccentFx mode={accent_fx} palette={palette}>{captionEl}</AccentFx>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
