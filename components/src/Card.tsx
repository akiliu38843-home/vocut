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
import { ComparisonPanel } from "./components/ComparisonPanel";
import { KeyNumber } from "./components/KeyNumber";
import { KeywordHighlight } from "./components/KeywordHighlight";
import { ListItem } from "./components/ListItem";
import { PullQuote } from "./components/PullQuote";
import { TitleCard } from "./components/TitleCard";
import { resolvePalette } from "./theme";

export const cardSchema = z.object({
  component: z.enum([
    "title_card",
    "key_number",
    "pull_quote",
    "comparison_panel",
    "list_item",
    "keyword_highlight",
  ]),
  /** Component-specific props. Permissive at the schema level. */
  props: z.record(z.string(), z.any()).optional(),
  /** Fallback display text when a component needs one and no specific prop is given. */
  sentence: z.string().optional(),
  /** Composition duration override; consumed by Root.calculateMetadata. */
  durationInFrames: z.number().int().positive().optional(),

  // ─── Variation knobs ─────────────────────────────────────────────────────
  /** Which color palette to use. Default: "editorial_dark". */
  palette: z.string().optional(),
  /** Background visual style. Default: "solid". */
  bg_style: z.enum(["solid", "gradient", "particles", "shader"]).optional(),
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
}) => {
  const p = (props ?? {}) as Record<string, unknown>;
  const palette = resolvePalette(paletteName);

  // Each component will be migrated to accept these as optional props.
  // For now we pass them through; components that haven't been migrated
  // simply ignore them (TS permits unknown props on React.FC).
  const motion = { palette, text_motion, accent_fx };

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
        return (
          <KeywordHighlight
            text={(p.text as string) ?? sentence ?? "?"}
            highlight={p.highlight as string | undefined}
            {...motion}
          />
        );
      default: {
        const _exhaustive: never = component;
        return <KeywordHighlight text={sentence ?? "?"} {...motion} />;
      }
    }
  })();

  return (
    <>
      <CardBackground palette={palette} bg_style={bg_style as BgStyle | undefined} />
      {body}
    </>
  );
};
