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
  const { width, height } = useVideoConfig();
  // Lottie 场景里动画是主角；caption 用 value (5%) 这个"次要主"级别
  const captionSize = Math.round(height * TYPE_RATIO.value);
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
      <AbsoluteFill style={{ opacity: lottie_opacity, overflow: "hidden" }}>
        {/*
          @remotion/lottie 默认按动画原生尺寸渲染 (800×600 之类). 用 transform
          scale 让它撑满容器 (cover): 取 max(w_ratio, h_ratio) 保证不留黑边.
          animationData.w / .h 是 Lottie JSON 里的 composition size.
        */}
        {(() => {
          const animW = (animationData as { w?: number }).w || 1280;
          const animH = (animationData as { h?: number }).h || 720;
          const scale = Math.max(width / animW, height / animH);
          return (
            <div
              style={{
                position: "absolute",
                left: "50%",
                top: "50%",
                width: animW,
                height: animH,
                transform: `translate(-50%, -50%) scale(${scale})`,
                transformOrigin: "center",
              }}
            >
              <Lottie animationData={animationData} loop />
            </div>
          );
        })()}
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
