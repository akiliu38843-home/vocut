/**
 * Claude-design-inspired color palette + typography tokens.
 * Editorial, restrained, dark-mode-friendly. No neon, no gradients.
 */

export const COLORS = {
  bg: {
    titleCard: "#000000",         // deepest dark, anchors chapter transitions
    keyNumber: "#0f172a",         // cool slate, evokes data
    pullQuote: "#1f1611",         // warm dark, evokes paper / archive
    comparisonLeft: "#0c1428",    // cool blue, side A
    comparisonRight: "#1f1611",   // warm brown, side B
    listItem: "#161616",          // neutral dark
    keywordHighlight: "#1a1a1a",  // neutral dark
  },
  text: {
    primary: "#ececea",           // off-white, softer than pure white
    secondary: "#9a9a96",         // muted gray for labels / attribution
    accent: "#d4a574",            // warm amber accent (key numbers, emphasis)
    quiet: "#5a5a56",             // very low contrast — corner labels
  },
} as const;

export const FONTS = {
  display:
    'ui-serif, "PingFang SC", "Source Han Serif SC", Georgia, "Times New Roman", serif',
  body:
    'ui-sans-serif, "PingFang SC", "Source Han Sans SC", -apple-system, "Helvetica Neue", sans-serif',
  mono: '"SF Mono", Menlo, Consolas, monospace',
} as const;

/** Easing curve. Slow-out, slow-in. No bounce. */
export const EASE_OUT_QUART = [0.165, 0.84, 0.44, 1] as const;
