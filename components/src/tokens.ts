/**
 * Design tokens — vocut 的"标尺"。
 *
 * 全部数值直接 mirror 自 Open Props (MIT, by Adobe's Adam Argyle),
 * 这样所有字号 / 空白 / 阴影 / 缓动都从同一张表里挑，
 * 不允许出现 28px / 12% 这种"我手感"的中间数。
 *
 * 在组件里用法:
 *   import { SIZE, FONT_SIZE, SHADOW, EASE } from "../tokens";
 *   <h1 style={{ fontSize: FONT_SIZE[8], padding: SIZE[6] }}>...</h1>
 */

// Open Props sizes (在 1rem = 16px 下展开成 px)
// 阶: 1=4 / 2=8 / 3=16 / 4=20 / 5=24 / 6=32 / 7=40 / 8=48 / 9=64
//     10=80 / 11=96 / 12=112 / 13=128 / 14=192 / 15=256
export const SIZE = {
  1: 4, 2: 8, 3: 16, 4: 20, 5: 24, 6: 32, 7: 40, 8: 48,
  9: 64, 10: 80, 11: 96, 12: 112, 13: 128, 14: 192, 15: 256,
} as const;

// Fluid font sizes (px). Open Props fluid version 在 1rem=16 下用最小端 + 一点偏大。
// 阶: 00=11 / 0=13 / 1=14 / 2=16 / 3=18 / 4=22 / 5=28 / 6=36 / 7=48 / 8=64 / 9=80
export const FONT_SIZE = {
  "00": 11, 0: 13, 1: 14, 2: 16, 3: 18, 4: 22,
  5: 28, 6: 36, 7: 48, 8: 64, 9: 80,
} as const;

// 字重 9 档
export const FONT_WEIGHT = {
  1: 100, 2: 200, 3: 300, 4: 400, 5: 500, 6: 600, 7: 700, 8: 800, 9: 900,
} as const;

// 行高 8 档
export const LINE_HEIGHT = {
  "00": 0.95, 0: 1.0, 1: 1.1, 2: 1.25, 3: 1.375, 4: 1.5, 5: 1.75, 6: 2.0,
} as const;

// 字间距 7 档（letter-spacing 用 em 比较稳）
export const LETTER_SPACING = {
  0: "-0.05em", 1: "-0.025em", 2: "0em", 3: "0.025em",
  4: "0.05em", 5: "0.075em", 6: "0.15em", 7: "0.5em",
} as const;

// Box shadow 7 档（Open Props 的简化版本，去掉了多层 HSL 变量）
export const SHADOW = {
  1: "0 1px 2px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.04)",
  2: "0 3px 5px -2px rgba(0, 0, 0, 0.05), 0 7px 14px -5px rgba(0, 0, 0, 0.06)",
  3: "0 -1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -2px rgba(0, 0, 0, 0.07), 0 2px 5px -3px rgba(0, 0, 0, 0.10), 0 4px 12px -5px rgba(0, 0, 0, 0.12)",
  4: "0 -2px 5px 0 rgba(0, 0, 0, 0.05), 0 1px 1px -2px rgba(0, 0, 0, 0.07), 0 2px 2px -2px rgba(0, 0, 0, 0.07), 0 5px 5px -2px rgba(0, 0, 0, 0.09), 0 9px 9px -2px rgba(0, 0, 0, 0.10), 0 16px 16px -2px rgba(0, 0, 0, 0.13)",
  5: "0 -1px 2px 0 rgba(0, 0, 0, 0.05), 0 2px 1px -2px rgba(0, 0, 0, 0.06), 0 5px 5px -2px rgba(0, 0, 0, 0.07), 0 10px 10px -3px rgba(0, 0, 0, 0.10), 0 20px 20px -4px rgba(0, 0, 0, 0.12), 0 30px 30px -5px rgba(0, 0, 0, 0.15)",
  6: "0 -1px 2px 0 rgba(0, 0, 0, 0.05), 0 2px 1px -2px rgba(0, 0, 0, 0.06), 0 5px 5px -2px rgba(0, 0, 0, 0.07), 0 10px 10px -3px rgba(0, 0, 0, 0.10), 0 24px 24px -8px rgba(0, 0, 0, 0.13), 0 40px 50px -8px rgba(0, 0, 0, 0.15)",
} as const;

// 缓动曲线 — Open Props 精选
export const EASE = {
  in1: "cubic-bezier(0.25, 0, 1, 1)",
  in2: "cubic-bezier(0.50, 0, 1, 1)",
  in3: "cubic-bezier(0.70, 0, 1, 1)",
  out1: "cubic-bezier(0, 0, 0.75, 1)",
  out2: "cubic-bezier(0, 0, 0.50, 1)",
  out3: "cubic-bezier(0, 0, 0.30, 1)",
  inOut1: "cubic-bezier(0.10, 0, 0.90, 1)",
  inOut2: "cubic-bezier(0.30, 0, 0.70, 1)",
  inOut3: "cubic-bezier(0.50, 0, 0.50, 1)",
  // Spring-feel
  spring1: "cubic-bezier(0.5, 1.25, 0.75, 1.25)",
  spring2: "cubic-bezier(0.3, 1.4, 0.45, 1.6)",
} as const;

// 圆角 6 档
export const RADIUS = {
  1: 2, 2: 5, 3: 8, 4: 12, 5: 20, 6: 32, round: 9999,
} as const;

// ─── 字号比例 ───────────────────────────────────────────────────────────────
// 按"屏幕高度的百分比"算字号，对齐行业标准:
//   - Netflix 字幕底线           4-5%
//   - YouTube/Vox 横屏知识视频   8-13% (主标题)
//   - Apple Keynote 演讲标题     7-10%
//   - TikTok/抖音/B站竖屏        10-15%
//   - CapCut 默认大字            12-15%
//
// 用法: const titleSize = Math.round(useVideoConfig().height * TYPE_RATIO.hero)
// 这样横屏自动小、竖屏自动大、不再死磕固定像素。
export const TYPE_RATIO = {
  hero:    0.090,   // title_card 主标题
  giant:   0.160,   // key_number 主数字 (它是整屏唯一焦点, 比 hero 还大)
  primary: 0.060,   // pull_quote / keyword_highlight 主文字
  value:   0.050,   // list_item / comparison_panel 单项
  body:    0.035,   // subtitle / attribution 等次要正文
  caption: 0.025,   // 副标 / 小说明
  label:   0.014,   // mono eyebrow / 大写小标签
  mono:    0.016,   // 监督文字 "01 / 16"
  numeral: 0.040,   // 列表序号
} as const;

// 字体堆 — Open Props 推荐的开源字体优先
// display: 衬线，正式 / editorial
// body: 无衬线，正文
// mono: 等宽，标签 / 编号
// 中文优先 Source Han (思源)，西文优先 IBM Plex（IBM 开源，质感比 Inter 沉）
export const FONT_STACK = {
  display:
    '"Source Han Serif SC", "Source Han Serif CN", "IBM Plex Serif", "Songti SC", Georgia, ui-serif, serif',
  body:
    '"Source Han Sans SC", "Source Han Sans CN", "IBM Plex Sans", "PingFang SC", -apple-system, "Helvetica Neue", ui-sans-serif, sans-serif',
  mono:
    '"IBM Plex Mono", "JetBrains Mono", "SF Mono", Menlo, Consolas, ui-monospace, monospace',
} as const;
