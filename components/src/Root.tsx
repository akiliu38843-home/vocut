import React from "react";
import { Composition } from "remotion";
import { Card, cardSchema } from "./Card";

const FPS = 30;
const DEFAULT_DURATION_FRAMES = 30 * 4; // 4 seconds @ 30fps; overridable via --frames

/**
 * Single composition that vocut renders into. Width / height / duration are
 * overridden per-invocation via Remotion CLI flags so one composition serves
 * all 5 components.
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
      defaultProps={{
        component: "title_card" as const,
        props: { title: "vocut", subtitle: "preview" },
      }}
    />
  );
};
