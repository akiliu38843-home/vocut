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

// ─── 动画 token (Phase W.1) ────────────────────────────────────────────────
//
// 数字来源 (调研可对照):
//   - Material Design 3   : stagger 40-120ms, 4 缓动曲线, 4 时长 token
//                          https://m3.material.io/styles/motion/easing-and-duration/tokens-specs
//   - Apple HIG Motion    : 200-400ms 标准, spring damping 0.7-1.0
//                          https://developer.apple.com/design/human-interface-guidelines/motion
//   - Nielsen Norman Group: sequence 2-5 物 300-400ms, 6-10 物 500-700ms
//                          https://www.nngroup.com/articles/animation-duration/
//
// 视频系数 ×1.5: UI 这些数字是给"用户看屏幕主动操作"用的, vocut 是观众**被动**看视频,
// 节奏要比 UI 慢 1.5 倍 (跟 transitions-charter.md §3 同标尺).
//
// 详见 docs/research/methodology/research-to-code-map.md §II.A

// 单位 ms - 单次动作 / 切换的持续时间
export const MOTION_DURATION = {
  instant: 100,     // 不到一眼, 几乎察觉不到
  fast: 300,        // 小元素出场 (Apple HIG 200 × 1.5)
  base: 500,        // 标准 (Apple HIG 300 × 1.5 ≈ NN/G sequence 2-5 物上限)
  slow: 800,        // 强调用 (Apple HIG <500 × 1.5)
  transition: 1200, // 场景级 (NN/G page transition 800 × 1.5)
} as const;

// 单位 ms - 父子元素 / 列表项之间排队间隔
export const MOTION_STAGGER = {
  tight: 80,        // 字与字 (Material 40 × 1.5 ≈ CMU 中文按字下限)
  normal: 120,      // 列表项 (Material 80 × 1.5 = vocut 默认 list stagger)
  loose: 180,       // 段落 / 大块 (Material 120 × 1.5)
} as const;

// Material Design 3 标准 4 缓动曲线 (cubic-bezier 控制点)
// 给 framer-motion / motion 用: animate={{ transition: { ease: MOTION_EASE.standard } }}
export const MOTION_EASE = {
  standard:   [0.2, 0, 0, 1],     // Material 默认: 通用 (本对本用)
  decelerate: [0, 0, 0.2, 1],     // 进入: 进场用 (东西从无到有)
  accelerate: [0.3, 0, 1, 1],     // 退出: 离场用 (东西从有到无)
  sharp:      [0.4, 0, 0.6, 1],   // 短切换: 临时元素 (toast / hover)
} as const;

// Apple HIG spring physics 配置
// 给 motion 用: <motion.div animate={{ x: 100 }} transition={MOTION_SPRING.gentle} />
//
// stiffness: 弹簧刚度, 越高越硬 (Apple 推荐 80-200)
// damping:   阻尼, 越高越快停 (Apple 推荐 12-20, damping/stiffness ≈ 0.07-0.1 对应 damping ratio 0.7-1.0)
export const MOTION_SPRING = {
  gentle: { type: "spring", stiffness: 120, damping: 14 } as const,  // 默认: 柔和过渡
  snappy: { type: "spring", stiffness: 200, damping: 12 } as const,  // 灵动: 弹一下 (Bounce-In)
} as const;
