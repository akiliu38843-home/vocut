/**
 * CardBackground — Layer 0 of every motion-graphic card.
 *
 * Renders behind the component body so particle / gradient / pseudo-shader
 * decoration can show through. Component bodies are foreground-only (no
 * AbsoluteFill bg fill of their own).
 *
 * Phase A.5 implements all 4 styles in pure CSS + DOM:
 *   solid     — flat palette.bg
 *   gradient  — diagonal linear-gradient palette.bg → palette.surface, drifts
 *   particles — 80 floating dots, randomized position + drift
 *   shader    — pseudo-WebGL via animated conic + radial gradient compositing
 *
 * No Three.js dependency to keep Remotion bundle lean (particle + shader looks
 * still feel motion-rich at 1280×720).
 */

import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import type { Palette } from "./theme";

export type BgStyle = "solid" | "gradient" | "particles" | "shader";

interface BgProps {
  palette: Palette;
  bg_style?: BgStyle;
}

// ─── solid ─────────────────────────────────────────────────────────────────
const SolidBg: React.FC<BgProps> = ({ palette }) => (
  <AbsoluteFill style={{ background: palette.bg }} />
);

// ─── gradient ──────────────────────────────────────────────────────────────
const GradientBg: React.FC<BgProps> = ({ palette }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  // Slow diagonal drift: 0 -> -30 degrees over 6 seconds.
  const angle = interpolate(frame, [0, fps * 6], [135, 105], {
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(${angle}deg, ${palette.bg} 0%, ${palette.surface} 60%, ${palette.bg} 100%)`,
      }}
    />
  );
};

// ─── particles ─────────────────────────────────────────────────────────────
const PARTICLE_COUNT = 80;
// Deterministic pseudo-random — same seed every render so frames are stable.
function prng(i: number, salt: number = 0): number {
  const x = Math.sin((i + 1) * 9.7 + salt * 17.3) * 43758.5453;
  return x - Math.floor(x);
}

const ParticlesBg: React.FC<BgProps> = ({ palette }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dots = Array.from({ length: PARTICLE_COUNT }, (_, i) => {
    const baseX = prng(i, 1) * 100;
    const baseY = prng(i, 2) * 100;
    const driftAmp = 1.5 + prng(i, 3) * 2;
    const driftSpeed = 0.5 + prng(i, 4) * 1.2;
    const driftOffset = prng(i, 5) * Math.PI * 2;
    const t = (frame / fps) * driftSpeed + driftOffset;
    const x = baseX + Math.sin(t) * driftAmp;
    const y = baseY + Math.cos(t * 0.7) * driftAmp;
    const size = 1.5 + prng(i, 6) * 3;
    const baseOpacity = 0.18 + prng(i, 7) * 0.42;
    const opacity = baseOpacity * (0.7 + 0.3 * Math.sin(t * 1.3));
    return { x, y, size, opacity, i };
  });
  return (
    <AbsoluteFill style={{ background: palette.bg, overflow: "hidden" }}>
      {dots.map((d) => (
        <div
          key={d.i}
          style={{
            position: "absolute",
            left: `${d.x}%`,
            top: `${d.y}%`,
            width: d.size,
            height: d.size,
            borderRadius: "50%",
            background: palette.accent,
            opacity: d.opacity,
            filter: "blur(0.5px)",
          }}
        />
      ))}
    </AbsoluteFill>
  );
};

// ─── shader (CSS-only pseudo-shader) ───────────────────────────────────────
const ShaderBg: React.FC<BgProps> = ({ palette }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  // Conic angle drifts; radial spot drifts; together they create a slow
  // volumetric feel reminiscent of an animated GLSL noise blob.
  const conicAngle = interpolate(frame, [0, fps * 8], [0, 360]);
  const spotX = 50 + Math.sin((frame / fps) * 0.6) * 18;
  const spotY = 50 + Math.cos((frame / fps) * 0.4) * 14;
  return (
    <AbsoluteFill style={{ background: palette.bg, overflow: "hidden" }}>
      <AbsoluteFill
        style={{
          background: `conic-gradient(from ${conicAngle}deg at 50% 50%, ${palette.bg}, ${palette.surface}, ${palette.bg}, ${palette.surface}, ${palette.bg})`,
          opacity: 0.55,
          filter: "blur(40px)",
        }}
      />
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at ${spotX}% ${spotY}%, ${palette.accent}33 0%, transparent 45%)`,
        }}
      />
    </AbsoluteFill>
  );
};

// ─── dispatcher ────────────────────────────────────────────────────────────
export const CardBackground: React.FC<BgProps> = ({ palette, bg_style }) => {
  switch (bg_style) {
    case "gradient":
      return <GradientBg palette={palette} />;
    case "particles":
      return <ParticlesBg palette={palette} />;
    case "shader":
      return <ShaderBg palette={palette} />;
    case "solid":
    default:
      return <SolidBg palette={palette} />;
  }
};
