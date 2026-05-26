/**
 * TextMotion — one wrapper, four entry styles for the primary text of a card.
 *
 *   fade       — opacity 0→1 + small Y nudge (default; matches Phase A entry)
 *   typewriter — characters appear one by one, no per-char fade
 *   wave       — characters stagger in with their own short fade + Y nudge
 *   scale_in   — content scales from 70% with a spring; whole element fades in
 *
 * Two API shapes:
 *   - Char-based modes (typewriter, wave) need the text as a string (use `text`)
 *   - Block-based modes (fade, scale_in) wrap arbitrary `children`
 *
 * If both are passed, mode decides which one is honored. If neither is passed,
 * an empty fragment is returned.
 */

import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

export type TextMotionMode = "fade" | "typewriter" | "wave" | "scale_in";

export interface TextMotionProps {
  mode?: TextMotionMode;
  /** Frame to start the animation, relative to the composition. Default 0. */
  startFrame?: number;
  /** How many frames the entry takes. Default ~0.5s at the current fps. */
  durationFrames?: number;
  /** Text to animate; required for typewriter / wave. */
  text?: string;
  /** Children to animate; honored by fade / scale_in. */
  children?: React.ReactNode;
  /** Optional style applied to the outer wrapper. */
  style?: React.CSSProperties;
}

export const TextMotion: React.FC<TextMotionProps> = ({
  mode = "fade",
  startFrame = 0,
  durationFrames,
  text,
  children,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = durationFrames ?? Math.round(fps * 0.5);
  const localFrame = Math.max(0, frame - startFrame);

  switch (mode) {
    case "typewriter": {
      if (!text) return <span style={style}>{children}</span>;
      const totalChars = [...text].length;
      const charsShown = Math.floor(
        interpolate(localFrame, [0, dur], [0, totalChars], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        }),
      );
      const visible = [...text].slice(0, charsShown).join("");
      // Blinking caret while typing
      const showCaret = charsShown < totalChars;
      return (
        <span style={style}>
          {visible}
          {showCaret && (
            <span
              style={{
                display: "inline-block",
                width: "0.06em",
                height: "0.95em",
                marginLeft: "0.04em",
                verticalAlign: "-0.1em",
                background: "currentColor",
                opacity: Math.floor(localFrame / 6) % 2 === 0 ? 0.9 : 0,
              }}
            />
          )}
        </span>
      );
    }

    case "wave": {
      if (!text) return <span style={style}>{children}</span>;
      const chars = [...text];
      const perChar = Math.max(1, Math.floor(dur / Math.max(1, chars.length)));
      return (
        <span style={style}>
          {chars.map((ch, i) => {
            const start = i * perChar;
            const op = interpolate(
              localFrame,
              [start, start + perChar * 2],
              [0, 1],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
            );
            const y = interpolate(
              localFrame,
              [start, start + perChar * 2],
              [12, 0],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
            );
            return (
              <span
                key={i}
                style={{
                  display: "inline-block",
                  opacity: op,
                  transform: `translateY(${y}px)`,
                  whiteSpace: "pre", // preserve spaces between chars
                }}
              >
                {ch}
              </span>
            );
          })}
        </span>
      );
    }

    case "scale_in": {
      const s = spring({ frame: localFrame, fps, config: { damping: 14, stiffness: 90 } });
      const opacity = interpolate(localFrame, [0, dur], [0, 1], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      });
      return (
        <span
          style={{
            display: "inline-block",
            transform: `scale(${0.72 + s * 0.28})`,
            opacity,
            ...style,
          }}
        >
          {children ?? text}
        </span>
      );
    }

    case "fade":
    default: {
      const opacity = interpolate(localFrame, [0, dur], [0, 1], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      });
      const y = interpolate(localFrame, [0, dur], [10, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      });
      return (
        <span
          style={{
            display: "inline-block",
            opacity,
            transform: `translateY(${y}px)`,
            ...style,
          }}
        >
          {children ?? text}
        </span>
      );
    }
  }
};
