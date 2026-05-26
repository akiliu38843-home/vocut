/**
 * LottieCard — long-tail motion-graphic slot.
 *
 * Renders a Lottie animation (from the bundled vocut/components/public/lottie/
 * pool, or any URL the user passes) as the back layer. A foreground text
 * block carries the script sentence, styled by the active palette.
 *
 * Used when no hand-coded component fits the scene — vocut plan looks up
 * the manifest tags and supplies a `lottie_id` (or `lottie_src` URL).
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
import { FONTS, PALETTES, type Palette } from "../theme";

export interface LottieCardProps {
  /** Lottie animation ID matching components/public/lottie/manifest.json. */
  lottie_id?: string;
  /** Override: explicit Lottie JSON URL or staticFile path. Wins over lottie_id. */
  lottie_src?: string;
  /** Overlay caption shown over the animation. */
  caption?: string;
  /** Animation back-layer opacity. Default 0.55 — keeps caption readable. */
  lottie_opacity?: number;
  palette?: Palette;
  text_motion?: TextMotionMode;
  accent_fx?: AccentFxMode;
}

export const LottieCard: React.FC<LottieCardProps> = ({
  lottie_id = "ripple",
  lottie_src,
  caption,
  lottie_opacity = 0.55,
  palette = PALETTES.editorial_dark,
  text_motion = "fade",
  accent_fx = "none",
}) => {
  const { fps } = useVideoConfig();
  const [animationData, setAnimationData] =
    useState<LottieAnimationData | null>(null);
  const [handle] = useState(() => delayRender(`lottie:${lottie_id}`));

  useEffect(() => {
    const url = lottie_src ?? staticFile(`lottie/${lottie_id}.json`);
    fetch(url)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status} on ${url}`);
        return r.json();
      })
      .then((data: LottieAnimationData) => {
        setAnimationData(data);
        continueRender(handle);
      })
      .catch((err) => {
        cancelRender(`Failed to load lottie ${lottie_id}: ${err.message}`);
      });
  }, [lottie_id, lottie_src, handle]);

  if (!animationData) {
    return <AbsoluteFill style={{ background: palette.bg }} />;
  }

  const isCharMode = text_motion === "typewriter" || text_motion === "wave";
  const captionStyle: React.CSSProperties = {
    margin: 0,
    fontFamily: FONTS.display,
    fontWeight: 500,
    fontSize: "clamp(48px, 6vw, 96px)",
    color: palette.text,
    textAlign: "center",
    lineHeight: 1.15,
    textShadow: `0 2px 24px ${palette.bg}cc`,
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
            justifyContent: "center",
            padding: "0 10%",
            zIndex: 2,
          }}
        >
          <AccentFx mode={accent_fx} palette={palette}>
            {captionEl}
          </AccentFx>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
