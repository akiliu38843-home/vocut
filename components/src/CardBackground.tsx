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
import { ThreeCanvas } from "@remotion/three";
import { Color } from "three";
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

// ─── shader (real WebGL via Three.js fragment shader) ──────────────────────
const SHADER_VERT = /* glsl */ `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const SHADER_FRAG = /* glsl */ `
  precision highp float;
  uniform float uTime;
  uniform vec3 uBg;
  uniform vec3 uSurface;
  uniform vec3 uAccent;
  uniform float uAspect;
  varying vec2 vUv;

  float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
  float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(
      mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x),
      mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x),
      u.y
    );
  }
  float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    for (int i = 0; i < 5; i++) {
      v += a * noise(p);
      p *= 2.0;
      a *= 0.5;
    }
    return v;
  }

  void main() {
    vec2 uv = vUv;
    uv.x *= uAspect;
    float n1 = fbm(uv * 2.5 + vec2(uTime * 0.08, uTime * 0.04));
    float n2 = fbm(uv * 1.8 + vec2(-uTime * 0.05, uTime * 0.09));
    vec3 base = mix(uBg, uSurface, smoothstep(0.3, 0.75, n1));
    vec3 col = mix(base, uAccent, smoothstep(0.62, 0.88, n2) * 0.30);
    float vig = smoothstep(1.25, 0.35, length(vUv - 0.5) * 1.5);
    col = mix(uBg, col, vig);
    gl_FragColor = vec4(col, 1.0);
  }
`;

const ShaderQuad: React.FC<{ palette: Palette }> = ({ palette }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const uniforms = React.useMemo(
    () => ({
      uTime: { value: 0 },
      uBg: { value: new Color(palette.bg) },
      uSurface: { value: new Color(palette.surface) },
      uAccent: { value: new Color(palette.accent) },
      uAspect: { value: width / height },
    }),
    // Recreate uniforms whenever palette changes so its colors update.
    [palette.bg, palette.surface, palette.accent, width, height],
  );
  // Per-frame uniform tick (mutates the existing uniform values in place).
  uniforms.uTime.value = frame / fps;
  return (
    <mesh>
      <planeGeometry args={[2, 2]} />
      <shaderMaterial
        vertexShader={SHADER_VERT}
        fragmentShader={SHADER_FRAG}
        uniforms={uniforms}
      />
    </mesh>
  );
};

const ShaderBg: React.FC<BgProps> = ({ palette }) => {
  const { width, height } = useVideoConfig();
  return (
    <AbsoluteFill style={{ background: palette.bg }}>
      <ThreeCanvas width={width} height={height}>
        <ShaderQuad palette={palette} />
      </ThreeCanvas>
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
