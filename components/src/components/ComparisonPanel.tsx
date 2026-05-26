import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { AccentFx, type AccentFxMode } from "../motion/AccentFx";
import { TextMotion, type TextMotionMode } from "../motion/TextMotion";
import { FONTS, PALETTES, type Palette } from "../theme";

export interface ComparisonItem {
  label?: string;
  value: string;
  tag?: string;
}

export interface ComparisonPanelProps {
  title?: string;
  items: ComparisonItem[];
  palette?: Palette;
  text_motion?: TextMotionMode;
  accent_fx?: AccentFxMode;
}

export const ComparisonPanel: React.FC<ComparisonPanelProps> = ({
  title,
  items,
  palette = PALETTES.editorial_dark,
  text_motion = "fade",
  accent_fx = "none",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const ruleProgress = interpolate(frame, [fps * 0.5, fps * 1.2], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const surfaces = items.map((_, i) =>
    i % 2 === 0 ? palette.bg : palette.surface,
  );

  const isCharMode = text_motion === "typewriter" || text_motion === "wave";

  return (
    <AbsoluteFill>
      {title && (
        <TextMotion mode="fade" durationFrames={Math.round(fps * 0.5)}>
          <div
            style={{
              position: "absolute",
              top: 48,
              left: 0,
              right: 0,
              textAlign: "center",
              fontFamily: FONTS.body,
              fontSize: 28,
              color: palette.textSecondary,
              letterSpacing: 4,
              textTransform: "uppercase",
              zIndex: 2,
            }}
          >
            {title}
          </div>
        </TextMotion>
      )}
      <div style={{ display: "flex", height: "100%", width: "100%" }}>
        {items.map((it, i) => {
          const itemStartFrame = Math.round(i * fps * 0.15);
          const valueStyle: React.CSSProperties = {
            fontFamily: FONTS.display,
            fontSize: "clamp(48px, 6vw, 84px)",
            color: palette.text,
            fontWeight: 400,
            textAlign: "center",
            lineHeight: 1.15,
          };
          const valueEl = isCharMode ? (
            <div style={valueStyle}>
              <TextMotion mode={text_motion} text={it.value} startFrame={itemStartFrame} />
            </div>
          ) : (
            <TextMotion mode={text_motion} startFrame={itemStartFrame}>
              <div style={valueStyle}>{it.value}</div>
            </TextMotion>
          );
          return (
            <div
              key={i}
              style={{
                flex: 1,
                background: surfaces[i],
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                padding: "0 4%",
                borderRight:
                  i < items.length - 1
                    ? `1px solid ${palette.quiet}`
                    : undefined,
              }}
            >
              {it.label && (
                <TextMotion mode="fade" startFrame={itemStartFrame} durationFrames={Math.round(fps * 0.4)}>
                  <div
                    style={{
                      fontFamily: FONTS.body,
                      fontSize: 22,
                      color: palette.textSecondary,
                      letterSpacing: 3,
                      textTransform: "uppercase",
                      marginBottom: 28,
                    }}
                  >
                    {it.label}
                  </div>
                </TextMotion>
              )}
              <AccentFx mode={accent_fx} palette={palette} startFrame={itemStartFrame}>
                {valueEl}
              </AccentFx>
              {it.tag && (
                <TextMotion mode="fade" startFrame={itemStartFrame + Math.round(fps * 0.3)}>
                  <div
                    style={{
                      marginTop: 24,
                      fontFamily: FONTS.mono,
                      fontSize: 22,
                      color: palette.accent,
                    }}
                  >
                    {it.tag}
                  </div>
                </TextMotion>
              )}
            </div>
          );
        })}
      </div>
      {items.length === 2 && (
        <div
          style={{
            position: "absolute",
            left: "50%",
            top: "20%",
            height: `${ruleProgress * 60}%`,
            width: 1,
            background: palette.quiet,
            transform: "translateX(-0.5px)",
          }}
        />
      )}
    </AbsoluteFill>
  );
};
