import React from "react";
import { Composition } from "remotion";
import { Card, cardSchema } from "./Card";

const FPS = 30;
const DEFAULT_DURATION_FRAMES = 30 * 4;

/**
 * Single composition that vocut renders into. Per-segment duration / width /
 * height come in via inputProps so one Card composition serves every motion
 * graphic. Pass `durationInFrames` in inputProps to override the default 120.
 */
export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Card"
      component={Card}
      schema={cardSchema}
      durationInFrames={DEFAULT_DURATION_FRAMES}
      fps={FPS}
      width={1280}
      height={720}
      calculateMetadata={({ props }) => {
        const m = props as { durationInFrames?: number };
        return {
          durationInFrames: m.durationInFrames ?? DEFAULT_DURATION_FRAMES,
        };
      }}
      defaultProps={{
        component: "title_card" as const,
        props: { title: "vocut", subtitle: "preview" },
      }}
    />
  );
};
