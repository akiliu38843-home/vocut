/**
 * Theme tokens for vocut motion graphics.
 *
 * Each palette is a self-contained 4-token set (bg / surface / text / accent).
 * Components receive a Palette object via Card props and read tokens from it
 * — they never reach into PALETTES directly. This lets the same component
 * render 8+ visually distinct variants from one codebase.
 */

export interface Palette {
  bg: string;        // page background
  surface: string;   // optional inner panel / card background
  text: string;      // primary type color
  textSecondary: string; // muted / labels
  accent: string;    // emphasis (key numbers, highlights, rules)
  quiet: string;     // corner labels, very low contrast
}

export type PaletteName =
  // ─── editorial pack ────────────────────────────────────────────────────
  | "editorial_dark"      // default — Claude-design black + amber
  | "cobalt_data"         // cool blue, "data" feel
  | "warm_paper"          // archive / book / quote
  | "gold_on_black"       // luxe / finance
  | "minimal_light"       // editorial light mode
  | "deep_purple"         // night sky, tech
  | "verdant"             // green oasis, nature / wellness
  | "ink_red"             // bold magazine red
  // ─── anime pack ───────────────────────────────────────────────────────
  | "sakura"              // 樱粉
  | "neon_purple"         // 霓虹紫 / vaporwave
  | "mikan"               // 蜜柑橙
  | "anime_noir"          // 黑金 / 成熟二次元
  | "matcha"              // 抹茶绿
  | "navy_white"          // 海军白蓝
  | "rose_gold"           // 玫瑰金
  | "dreamy_pastel";      // 梦境粉紫

export const PALETTES: Record<PaletteName, Palette> = {
  editorial_dark: {
    bg: "#000000",
    surface: "#161616",
    text: "#ececea",
    textSecondary: "#9a9a96",
    accent: "#d4a574",
    quiet: "#5a5a56",
  },
  cobalt_data: {
    bg: "#0f172a",
    surface: "#1e293b",
    text: "#e2e8f0",
    textSecondary: "#94a3b8",
    accent: "#60a5fa",
    quiet: "#475569",
  },
  warm_paper: {
    bg: "#1f1611",
    surface: "#2a1f17",
    text: "#f5ebe0",
    textSecondary: "#a89684",
    accent: "#e3a072",
    quiet: "#6e5d4f",
  },
  gold_on_black: {
    bg: "#0a0a0a",
    surface: "#1a1a18",
    text: "#f4e8c8",
    textSecondary: "#8a7d5e",
    accent: "#d4af37",
    quiet: "#4d4533",
  },
  minimal_light: {
    bg: "#fafaf7",
    surface: "#ffffff",
    text: "#1a1a1a",
    textSecondary: "#6b6b66",
    accent: "#c2410c",
    quiet: "#b0b0a8",
  },
  deep_purple: {
    bg: "#1a0f2e",
    surface: "#2a1e44",
    text: "#ede9fe",
    textSecondary: "#a78bd6",
    accent: "#c4b5fd",
    quiet: "#5b4c7a",
  },
  verdant: {
    bg: "#0a2a1f",
    surface: "#143a2e",
    text: "#ecfdf5",
    textSecondary: "#86e2b8",
    accent: "#bef264",
    quiet: "#3a6a52",
  },
  ink_red: {
    bg: "#1a0808",
    surface: "#2a1414",
    text: "#fef2f2",
    textSecondary: "#d4a4a4",
    accent: "#dc2626",
    quiet: "#5a3434",
  },

  // ─── anime pack ─────────────────────────────────────────────────────────
  sakura: {
    bg: "#2d1a26",
    surface: "#3f2433",
    text: "#fdf2f5",
    textSecondary: "#e8b5c8",
    accent: "#f472b6",
    quiet: "#6b4754",
  },
  neon_purple: {
    bg: "#0c0a1f",
    surface: "#1a163d",
    text: "#f0e6ff",
    textSecondary: "#a78bfa",
    accent: "#ff4dff",
    quiet: "#3e3463",
  },
  mikan: {
    bg: "#2a1810",
    surface: "#3d2418",
    text: "#fff5e8",
    textSecondary: "#fbbf24",
    accent: "#fb923c",
    quiet: "#5f3f28",
  },
  anime_noir: {
    bg: "#0a0a0a",
    surface: "#1a1a18",
    text: "#f5e8c8",
    textSecondary: "#c4ab6e",
    accent: "#fbbf24",
    quiet: "#4d4533",
  },
  matcha: {
    bg: "#1a2a1e",
    surface: "#2a3d2e",
    text: "#f0fdf4",
    textSecondary: "#86efac",
    accent: "#a3e635",
    quiet: "#4a6353",
  },
  navy_white: {
    bg: "#1e2a3d",
    surface: "#2a3b54",
    text: "#f1f5f9",
    textSecondary: "#94a3b8",
    accent: "#38bdf8",
    quiet: "#475569",
  },
  rose_gold: {
    bg: "#2a1a1e",
    surface: "#3d2630",
    text: "#fdf2f8",
    textSecondary: "#fb7185",
    accent: "#fda4af",
    quiet: "#5f3c4a",
  },
  dreamy_pastel: {
    bg: "#1f1a3d",
    surface: "#2a2354",
    text: "#f0e7ff",
    textSecondary: "#c4b5fd",
    accent: "#fbcfe8",
    quiet: "#50467a",
  },
};

export const DEFAULT_PALETTE_NAME: PaletteName = "editorial_dark";

/** Resolve a palette name (or undefined) to a Palette object. */
export function resolvePalette(name?: string): Palette {
  if (name && name in PALETTES) {
    return PALETTES[name as PaletteName];
  }
  return PALETTES[DEFAULT_PALETTE_NAME];
}

// -----------------------------------------------------------------------------
// Back-compat (existing components still reference COLORS.bg.* / COLORS.text.*)
// -----------------------------------------------------------------------------
// These keep the original API working until each component is migrated to read
// `palette` from props. New components should use Palette directly.

const D = PALETTES.editorial_dark;
const COBALT = PALETTES.cobalt_data;
const WARM = PALETTES.warm_paper;

export const COLORS = {
  bg: {
    titleCard: D.bg,
    keyNumber: COBALT.bg,
    pullQuote: WARM.bg,
    comparisonLeft: "#0c1428",
    comparisonRight: "#1f1611",
    listItem: D.surface,
    keywordHighlight: D.surface,
  },
  text: {
    primary: D.text,
    secondary: D.textSecondary,
    accent: D.accent,
    quiet: D.quiet,
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
