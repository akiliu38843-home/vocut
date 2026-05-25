/**
 * Card — the single Remotion composition entry point that dispatches to
 * one of the 5 motion-graphic components based on the `component` prop.
 *
 * This is what vocut's Python render layer calls via:
 *   npx remotion render src/Root.tsx Card output.mp4 --props='...'
 *
 * The Python side never has to know about React; it just passes a JSON
 * blob matching the props.json schema below.
 */

import React from "react";
import { z } from "remotion";
import { ComparisonPanel } from "./components/ComparisonPanel";
import { KeyNumber } from "./components/KeyNumber";
import { KeywordHighlight } from "./components/KeywordHighlight";
import { ListItem } from "./components/ListItem";
import { PullQuote } from "./components/PullQuote";
import { TitleCard } from "./components/TitleCard";

export const cardSchema = z.object({
  component: z.enum([
    "title_card",
    "key_number",
    "pull_quote",
    "comparison_panel",
    "list_item",
    "keyword_highlight",
  ]),
  // `props` is component-specific; we keep it permissive at the schema level
  // and let each component's TS types document its expected shape.
  props: z.record(z.string(), z.any()).optional(),
  /**
   * Fallback display text used when the matched component is keyword_highlight
   * and the caller hasn't supplied an explicit `text` prop — vocut just hands
   * the script sentence here so the card is never empty.
   */
  sentence: z.string().optional(),
});

export type CardProps = z.infer<typeof cardSchema>;

export const Card: React.FC<CardProps> = ({ component, props, sentence }) => {
  const p = (props ?? {}) as Record<string, unknown>;

  switch (component) {
    case "title_card":
      return (
        <TitleCard
          title={(p.title as string) ?? sentence ?? "untitled"}
          subtitle={p.subtitle as string | undefined}
          eyebrow={p.eyebrow as string | undefined}
        />
      );
    case "key_number":
      return (
        <KeyNumber
          primary={(p.primary as string) ?? "?"}
          unit={p.unit as string | undefined}
          label={p.label as string | undefined}
          secondary={p.secondary as string | undefined}
        />
      );
    case "pull_quote":
      return (
        <PullQuote
          quote={(p.quote as string) ?? sentence ?? "—"}
          attribution={p.attribution as string | undefined}
        />
      );
    case "comparison_panel": {
      // Accept either the canonical {items: [{label, value, tag}, ...]} shape
      // or a convenience {left, right} shape.
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
      return <ComparisonPanel title={p.title as string | undefined} items={items} />;
    }
    case "list_item": {
      const items = (p.items as string[]) ?? (sentence ? [sentence] : ["?"]);
      return (
        <ListItem
          items={items}
          label={p.label as string | undefined}
          style={p.style as "decimal" | "none" | undefined}
        />
      );
    }
    case "keyword_highlight":
      return (
        <KeywordHighlight
          text={(p.text as string) ?? sentence ?? "?"}
          highlight={p.highlight as string | undefined}
        />
      );
    default: {
      // exhaustiveness check — TS will error if a new component isn't handled
      const _exhaustive: never = component;
      return <KeywordHighlight text={sentence ?? "?"} />;
    }
  }
};
