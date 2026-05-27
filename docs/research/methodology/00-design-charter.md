# vocut 美学宪法

本文 = 6 个开源设计方法论站归一出的 vocut 必须遵守的硬规则。
每条改动必须回指这里某条规则。不是我手感，是行业共识。

参考文档：
- [Refactoring UI 7 原则](./refactoring-ui.md)
- [Practical Typography (Butterick)](./butterick-typography.md)
- [BBC GEL Typography](./bbc-gel-typography.md)
- [Material Motion (M1+M3)](./material-motion.md)
- [Carbon Motion (IBM)](./carbon-motion.md)
- [Atlassian Motion](./atlassian-motion.md)
- [Apple HIG Motion](./apple-hig-motion.md)

---

## §1 字体

### §1.1 字体堆只允许 2 个家族（来自 Butterick + Refactoring UI 5）
- 一个**显示字体**（serif，主标题用）
- 一个**正文字体**（sans-serif，body / label / 副标）
- mono 是辅助第 3 个，只能用于数字、编号、监督文字，**不能用于正文**
- **vocut 选定**：
  - display: Source Han Serif → 思源宋体（中文）+ IBM Plex Serif（西文/数字）
  - body: Source Han Sans → 思源黑体 + IBM Plex Sans
  - mono: IBM Plex Mono / JetBrains Mono

### §1.2 字号阶梯（屏高百分比 — 按 BBC GEL + Material 节奏）
| 角色 | 屏高% | 1080×1920 实测 | 1280×720 实测 |
|---|---|---|---|
| hero 主标题（title_card） | 9% | 173px | 65px |
| giant 大数字（key_number） | 14-16% | 269-307px | 100-115px |
| primary（pull_quote / 高亮句） | 5-6% | 96-115px | 36-43px |
| value（list / comparison item） | 4-5% | 77-96px | 29-36px |
| body（subtitle / attribution） | 3-3.5% | 57-67px | 22-25px |
| label（eyebrow / 大写小标签） | 1.3-1.5% | 25-29px | 9-11px |

### §1.3 行高 leading（来自 BBC GEL + Butterick）
- body: **1.5**（BBC GEL minimum / WCAG）
- display 大标题: **1.1-1.25**（紧凑、视觉冲击）
- 引号 / italic: **1.35**（呼吸感）

### §1.4 字间距 letter-spacing
- 大写小标签（mono / eyebrow）: **+5% 到 +12%**（Butterick）
- 大标题 display: **-2.5% 到 -5%**（紧凑）
- 正文 body: **0**

### §1.5 字数与折行（Butterick）
- 一行长度**控制在 45-90 字符**（拉丁文 char）/ **20-30 个汉字**
- 超过强制折行；不要让文字横跨整屏

---

## §2 留白 spacing

### §2.1 间距阶梯（Open Props 标尺，源自 8pt grid 行业共识）
全部从这张标尺挑数：**4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48 / 64 / 80 / 96 / 112 / 128px**

### §2.2 留白 > 装饰（Refactoring UI 3）
- "Start with excessive white space, then reduce" — 先大量留白，再删减，不是反过来
- 文字四周永远有 **≥ 5% 屏宽** 的安全边距
- 元素之间间距**遵循"相关 vs 不相关"原则**（BBC GEL）：相关元素小间距，不相关大间距，且差异至少 2x

---

## §3 动效 motion

### §3.1 时长（按 Apple + Material + Atlassian 共识）
| 类型 | 时长 | 用场 |
|---|---|---|
| **fast** | 70-150ms | 不重要的小元素入场（如 monitor 文字、装饰条）|
| **moderate** | 150-400ms | **vocut 主流**：标题入场、数字 scale-in、引言淡入 |
| **slow** | 400-700ms | 大跨度移动、章节过场 |
| **禁止区** | <50ms 或 >1000ms | 太快观众看不到，太慢觉得卡 |

### §3.2 缓动曲线（直接拿 Material + Carbon 的真值，不自创）
| 用场 | cubic-bezier | 来自 |
|---|---|---|
| **入场** decelerate | `cubic-bezier(0, 0, 0.2, 1)` | Material |
| **出场** accelerate | `cubic-bezier(0.4, 0, 1, 1)` | Material |
| **状态切换** standard | `cubic-bezier(0.2, 0, 0, 1)` | Material 3 |
| **品牌时刻** emphasized | `cubic-bezier(0.05, 0.7, 0.1, 1)` | Material 3 (decelerate variant) |
| **数据密集场景** productive | `cubic-bezier(0.2, 0, 0.38, 0.9)` | Carbon |

### §3.3 动效配对原则（Atlassian + Material）
- **入场和出场必须配对**：用 decelerate 入场就用 accelerate 出场（同一系列）
- **出场比入场快**（Atlassian）：避免观众等
- **小元素快 / 大元素慢**（Carbon "duration is dynamic"）

### §3.4 同屏动效最多 2 个并行（Atlassian "Wrong"）
- 多个动效同时跑会"抢观众注意力"
- vocut 每个 scene 只有 1 个主动效（主文字入场），其他静止

---

## §4 装饰 decoration

### §4.1 装饰必须锚定内容（Refactoring UI 1）
- "Use fewer borders" — 用阴影 / 颜色对比 / 间距替代多余的线和框
- **任何装饰元素都必须紧贴或重叠于一个具体内容**（不能浮空挂在画面 5% 处）
- 装饰要么强化层次，要么删

### §4.2 单一焦点原则（Atlassian "Single focal point leads"）
- 每个 scene 只有 1 个视觉焦点
- 其他元素都是它的伴奏（小、淡、靠边）

### §4.3 装饰数量上限 / scene（vocut 内部硬规则）
| 维度 | 上限 |
|---|---|
| 主文字 | 1 块 |
| 副文字 / label | 1-2 块 |
| 装饰元素（线、点、图标、Lottie 背景）| **0-1 个** |
| 背景层 | 1 层（纯色 / 渐变 / 视频，三选一） |

**禁止**：背景 + Lottie + AccentFx + 监督文字 + 主文字 + 副文字 同屏 6 层。

---

## §5 颜色 color

### §5.1 起步灰度，最后加颜色（Refactoring UI 1）
- 设计先在黑白稿能读通，再加颜色
- 颜色不撑层次，**字号 + 字重 + 对比** 才撑层次

### §5.2 颜色数量（Refactoring UI 5）
- 一个 palette 最多: 1 bg + 1 surface + 1 text + 1 textSecondary + 1 accent + 1 quiet = **6 色**
- 一个 scene 最多用 3 个颜色（含背景）
- accent 颜色每 scene **只用 1 次** — 在主焦点上

### §5.3 对比度（WCAG 标准，BBC GEL 隐含要求）
- 正文文字 / 背景对比度 ≥ 4.5:1
- 大标题 / 背景对比度 ≥ 3:1
- 装饰文字 / 背景对比度 ≥ 3:1 但允许低（视觉次序）

---

## §6 vocut 的硬反则（来自上面所有，集合负面清单）

❌ **不允许**:
1. 装饰浮空挂在画面里（不锚定内容）
2. 一个 scene 超过 2 个装饰元素
3. 字号不在 §1.2 阶梯上（28/44/72 这种手感数）
4. 间距不在 §2.1 阶梯上（5% / 12% 这种手感数）
5. 缓动曲线自创（必须从 §3.2 拿）
6. 文字 + 背景对比度 < 3:1
7. 一帧超过 3 个颜色（含背景）
8. 多个动效同时入场（同帧最多 1 个 spring + 1 个 fade）
9. 字体家族超过 3 个（display + body + mono 已是上限）
10. 装饰摆出来没有特定的内容关系（"为什么它要在这"答不上来就不加）

---

## §7 vocut 当前问题 vs 宪法（自检）

| 现在做的 | 违反第几条 |
|---|---|
| SceneFrame 浮空"01/16"监督 + 上下横线 | §4.1（不锚定）+ §4.3（装饰超量） |
| anime pack 的 danmaku 弹幕背景 | §4.1（弹幕跟内容没关系） |
| AccentFx 的 burst 6 条放射线 | §4.1 + §4.3 |
| 一帧叠 5 层（bg+frame+lottie+text+fx） | §4.3 |
| 16 套 palette 凭手感选 | §5.2（颜色超量） |
| 字号自定 28/44/72 | §1.2（不在阶梯上） |
| 缓动曲线自创 | §3.2（应该用 Material/Carbon 真值） |

**结论**：vocut 现在违反宪法 **7 / 10** 条。下一步重做必须照宪法。
