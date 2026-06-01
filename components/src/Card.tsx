/**
 * Card — the single Remotion composition entry point that dispatches to
 * one of the 6 motion-graphic components based on the `component` prop,
 * and wraps it in a configurable background layer.
 *
 * vocut's Python render layer calls this via:
 *   npx remotion render src/index.ts Card output.mp4 --props=<file.json>
 *
 * The Python side never has to know about React; it just passes a JSON
 * blob matching the props.json schema below.
 */

import React from "react";
import { z } from "zod";
import { CardBackground, type BgStyle } from "./CardBackground";
import { SceneFrame } from "./SceneFrame";
import type { AccentFxMode } from "./motion/AccentFx";
import type { TextMotionMode } from "./motion/TextMotion";
import { ComparisonPanel } from "./components/ComparisonPanel";
import { KeyNumber } from "./components/KeyNumber";
import { KeywordHighlight } from "./components/KeywordHighlight";
import { ListItem } from "./components/ListItem";
import { LottieCard } from "./components/LottieCard";
import { PullQuote } from "./components/PullQuote";
import { TitleCard } from "./components/TitleCard";
import {
  DynamicConceptMap,
  DynamicHighlight,
  DynamicList,
  DynamicNumber,
  DynamicQuote,
} from "./components-dynamic";
import { resolvePalette } from "./theme";

// Phase W.4: 动态版组件总开关. 默认 ON (走 Dynamic), env VOCUT_STATIC=1 走老组件回退.
// vocut Python 渲染时通过 `--env VOCUT_STATIC=1` 传给 Remotion CLI.
const USE_DYNAMIC =
  typeof process !== "undefined"
    ? process.env.VOCUT_STATIC !== "1"
    : true;

export const cardSchema = z.object({
  component: z.enum([
    "title_card",
    "key_number",
    "pull_quote",
    "comparison_panel",
    "list_item",
    "keyword_highlight",
    "lottie",
    "concept_map",
  ]),
  /** Component-specific props. Permissive at the schema level. */
  props: z.record(z.string(), z.any()).optional(),
  /** Fallback display text when a component needs one and no specific prop is given. */
  sentence: z.string().optional(),
  /** Composition duration override; consumed by Root.calculateMetadata. */
  durationInFrames: z.number().int().positive().optional(),

  // ─── SceneFrame metadata ─────────────────────────────────────────────────
  /** 0-indexed position of this scene in the full plan (for "01/16" monitor). */
  scene_idx: z.number().int().nonnegative().optional(),
  /** Total number of scenes in the plan. */
  total_scenes: z.number().int().positive().optional(),
  /** Section label shown in the monitor text. */
  section_label: z.string().optional(),
  /** Active style pack name — controls frame decoration style. */
  style_pack: z.string().optional(),

  // ─── Variation knobs ─────────────────────────────────────────────────────
  /** Which color palette to use. Default: "editorial_dark". */
  palette: z.string().optional(),
  /** Background visual style. Default: "solid". */
  bg_style: z.enum(["solid", "gradient", "particles", "shader", "sakura", "danmaku"]).optional(),
  /** How content text enters. Default: component-specific. */
  text_motion: z.enum(["fade", "typewriter", "wave", "scale_in"]).optional(),
  /** Decoration accent. Default: "none". */
  accent_fx: z.enum(["none", "glow", "burst", "underline_sweep"]).optional(),
});

export type CardProps = z.infer<typeof cardSchema>;

export const Card: React.FC<CardProps> = ({
  component,
  props,
  sentence,
  palette: paletteName,
  bg_style,
  text_motion,
  accent_fx,
  scene_idx,
  total_scenes,
  section_label,
  style_pack,
}) => {
  const p = (props ?? {}) as Record<string, unknown>;
  const palette = resolvePalette(paletteName);
  const motion = {
    palette,
    text_motion: text_motion as TextMotionMode | undefined,
    accent_fx: accent_fx as AccentFxMode | undefined,
  };

  const body = (() => {
    switch (component) {
      case "title_card":
        return (
          <TitleCard
            title={(p.title as string) ?? sentence ?? "untitled"}
            subtitle={p.subtitle as string | undefined}
            eyebrow={p.eyebrow as string | undefined}
            {...motion}
          />
        );
      case "key_number":
        if (USE_DYNAMIC) {
          return (
            <DynamicNumber
              primary={(p.primary as string) ?? "?"}
              unit={p.unit as string | undefined}
              label={p.label as string | undefined}
              secondary={p.secondary as string | undefined}
              palette={motion.palette}
              durationMs={p.duration_ms as number | undefined}
            />
          );
        }
        return (
          <KeyNumber
            primary={(p.primary as string) ?? "?"}
            unit={p.unit as string | undefined}
            label={p.label as string | undefined}
            secondary={p.secondary as string | undefined}
            {...motion}
          />
        );
      case "pull_quote":
        if (USE_DYNAMIC) {
          return (
            <DynamicQuote
              quote={(p.quote as string) ?? sentence ?? "—"}
              attribution={p.attribution as string | undefined}
              palette={motion.palette}
              staggerMs={p.stagger_ms as number | undefined}
            />
          );
        }
        return (
          <PullQuote
            quote={(p.quote as string) ?? sentence ?? "—"}
            attribution={p.attribution as string | undefined}
            {...motion}
          />
        );
      case "comparison_panel": {
        let items: Array<{ label?: string; value: string; tag?: string }>;
        if (Array.isArray(p.items)) {
          items = p.items as Array<{ label?: string; value: string; tag?: string }>;
        } else {
          const left = p.left;
          const right = p.right;
          items = [
            typeof left === "string"
              ? { value: left }
              : (left as { label?: string; value: string; tag?: string }) ?? { value: "?" },
            typeof right === "string"
              ? { value: right }
              : (right as { label?: string; value: string; tag?: string }) ?? { value: "?" },
          ];
        }
        return (
          <ComparisonPanel
            title={p.title as string | undefined}
            items={items}
            {...motion}
          />
        );
      }
      case "list_item": {
        const items = (p.items as string[]) ?? (sentence ? [sentence] : ["?"]);
        if (USE_DYNAMIC) {
          return (
            <DynamicList
              items={items}
              label={p.label as string | undefined}
              style={p.style as "decimal" | "none" | undefined}
              palette={motion.palette}
              staggerMs={p.stagger_ms as number | undefined}
              itemDurationMs={p.item_duration_ms as number | undefined}
            />
          );
        }
        return (
          <ListItem
            items={items}
            label={p.label as string | undefined}
            style={p.style as "decimal" | "none" | undefined}
            {...motion}
          />
        );
      }
      case "keyword_highlight":
        if (USE_DYNAMIC) {
          return (
            <DynamicHighlight
              text={(p.text as string) ?? sentence ?? "?"}
              highlight={p.highlight as string | undefined}
              palette={motion.palette}
              staggerMs={p.stagger_ms as number | undefined}
            />
          );
        }
        return (
          <KeywordHighlight
            text={(p.text as string) ?? sentence ?? "?"}
            highlight={p.highlight as string | undefined}
            {...motion}
          />
        );
      case "lottie":
        return (
          <LottieCard
            lottie_id={p.lottie_id as string | undefined}
            lottie_src={p.lottie_src as string | undefined}
            caption={(p.caption as string) ?? sentence}
            lottie_opacity={p.lottie_opacity as number | undefined}
            {...motion}
          />
        );
      case "concept_map":
        return (
          <DynamicConceptMap
            nodes={(p.nodes as Array<{ id: string; label: string; x: number; y: number }>) ?? []}
            edges={(p.edges as Array<{ from: string; to: string; label?: string }>) ?? []}
            keyframes={(p.keyframes as Array<{ id: string; atSec: number }>) ?? []}
            palette={motion.palette}
            fadeInDurationMs={p.fade_in_duration_ms as number | undefined}
          />
        );
      default: {
        const _exhaustive: never = component;
        return <KeywordHighlight text={sentence ?? "?"} {...motion} />;
      }
    }
  })();

  // LottieCard supplies its own background layer (the animation), so
  // suppressing CardBackground avoids paint over.
  const showCardBg = component !== "lottie";

  return (
    <>
      {showCardBg && <CardBackground palette={palette} bg_style={bg_style as BgStyle | undefined} />}
      <SceneFrame
        palette={palette}
        style_pack={style_pack}
        scene_idx={scene_idx}
        total_scenes={total_scenes}
        section_label={section_label}
      >
        {body}
      </SceneFrame>
    </>
  );
};
