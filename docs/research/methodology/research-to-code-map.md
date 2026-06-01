# vocut 调研 → 代码 完整落点映射

> **2026-05-29** · 把过去 K 阶段以来所有调研 (V.1-V.8 含 K/L/M/N/O/P/Q/R/S/T/U) 跟具体代码 / 文件 / 数字 / LLM prompt 章节对应清楚
> 用法: 任何 Claude session 接手 vocut 都先读这页, 知道每个调研的"代码落点 + 状态"

---

## 三类调研落地方式

| 类型 | 落点 | 例子 |
|---|---|---|
| **类 1 · 真依赖** | `package.json` npm install | framer-motion, Remotion, Lottie |
| **类 2 · 数字** | `tokens.ts` / `plan.py` 硬编码常量 | Material 缓动 4 曲线, BBC 字幕 0.3s/字 |
| **类 3 · prompt 知识** | `LLM_SYSTEM_PROMPT` 章节 | 10 套路名 / Murch 六法则 / Dmytryk 七律 |

每个调研结果**至少落一处**, 否则视为"调研了但没用"。

---

## I · 真依赖矩阵 (package.json)

| 调研 / 工具 | 来自哪轮 | 落点 | 状态 |
|---|---|---|---|
| **Remotion** + 各 sub-package | 基础 | `components/package.json` | ✅ 已装 |
| **Open Props** | R.1 | `components/package.json` | ✅ 已装 (基础 design token 库) |
| **@remotion/lottie** + lottie-web | O 阶段 | `components/package.json` | ✅ 已装 |
| **@remotion/captions** | Q.1 | `components/package.json` | ✅ 已装 |
| **@react-three/fiber + three** | 早期 P | `components/package.json` | ✅ 已装 (但少用) |
| **framer-motion** | **V.8 第一轮** | `components/package.json` | ⏭️ **W.1 待装** |
| ~~Manim CE~~ | V.8 第一轮 | 暂不装 | ❌ 数学题视频时再说 |
| ~~Motion Canvas / GSAP / theatre.js / movis~~ | V.8 第一轮 实测已死 | 永不装 | ❌ |
| **TransNetV2** | V.6 | 暂不装 | ⏭️ V.7 实测 (用户跳过) |

---

## II · 数字矩阵 (tokens.ts + plan.py 硬编码)

### II.A · 视觉 token (`components/src/tokens.ts`)

| 调研出处 | 具体数字 | 落在 tokens.ts 哪个常量 | 状态 |
|---|---|---|---|
| Open Props 4-tier 字号 | 9% / 6% / 5% / 3.5% / 2.5% / 1.4% | `TYPE_RATIO.*` (按屏高 %) | ✅ N.1 已落 |
| Material spacing | 8 / 16 / 24 / 32 / 48 | `SIZE.*` | ✅ L.1 已落 |
| BBC GEL 字重 / 字间距 | 各值 | `FONT_WEIGHT.*` / `LETTER_SPACING.*` | ✅ L.1 已落 |
| Butterick 行高 1.2-1.5 | 1.1 / 1.25 / 1.4 / 1.6 | `LINE_HEIGHT.*` | ✅ L.1 已落 |
| Refactoring UI 阴影 | 0/2/4/8 等 | `SHADOW.*` | ✅ L.1 已落 |
| Material 默认 ease | `[0.4, 0, 0.2, 1]` | `EASE.standard` | ✅ L.1 已落 |
| **Material 3 缓动 4 曲线** | `[0.2,0,0,1]` 等 4 套 | **`MOTION_EASE.standard/decelerate/accelerate/sharp`** | ⏭️ **W.1 待落** |
| **Material stagger 40-120ms × 视频系数 1.5** | 60 / 120 / 180 ms | **`MOTION_STAGGER.tight/normal/loose`** | ⏭️ **W.1 待落** |
| **Apple HIG 200-400ms × 1.5** | 300 / 500 / 800 / 1200 ms | **`MOTION_DURATION.fast/base/slow/transition`** | ⏭️ **W.1 待落** |
| **Apple spring damping 0.7-1.0** | damping 12-14 | **`MOTION_SPRING.gentle/snappy`** | ⏭️ **W.1 待落** |

### II.B · plan.py 算法常量 (`src/vocut/plan.py`)

| 调研出处 | 常量 / 函数 | 状态 |
|---|---|---|
| Walter Murch 六法则权重 | `LLM_SYSTEM_PROMPT § 0` (RERANK_TOOL 加 emotion_beat/narrative_role/pacing_intent) | ✅ V.2 已落 |
| BBC 字幕停留 0.3s/字 | `_bbc_min_duration_for_props()` | ✅ V.2 已落 |
| Cinemetrics 短视频 ASL / B 站基准 | `_cinemetrics_advisory()` (warning 不阻塞) | ✅ V.2 已落 (5.0s 编的, 标 TODO) |
| 组件基线时长 | `COMPONENT_BASELINE_SEC` | ✅ V.2 已落 |
| pacing 倍率 0.7/1.0/1.4 | `PACING_MULTIPLIER` | ✅ V.2 已落 |
| Eisenstein 五蒙太奇 | 暂不落 | ⏭️ 第 1 层 (节拍) 已部分落, 调性/智性留 |
| **B 站 8-12 分钟黄金区** (V.6 huasheng) | `TARGET_VIDEO_MINUTES` (待加) | ⏭️ **待落** |
| **B 站 Hook 三元素 (前 30s)** | `_validate_chapter_pacing()` (待写) | ⏭️ **待落** |
| **B 站冷区 < 2 分钟** | 同上 | ⏭️ **待落** |
| 转场 4 种 / 18 帧基线 | `TRANSITION_DURATION_FRAMES` + `_assign_transitions()` | ✅ U.4 已落 |
| ~~AutoShot 快手 2.97s~~ | 不落 (不对位) | ❌ 封存 |
| ~~Tiger200K 121 帧 5 秒~~ | 不落 (不对位) | ❌ 封存 |

---

## III · LLM Prompt 章节矩阵 (`plan.py LLM_SYSTEM_PROMPT`)

| 调研出处 | LLM prompt 章节 | 教 LLM 什么 | 状态 |
|---|---|---|---|
| v0 (Vercel) system prompt 框架 | § A-G 整体框架 | 选 type / 组件 / 色板 / 排版 / 留白 / 风格 / 反则 | ✅ T.1 已落 |
| **Murch 六法则 (情绪/故事/节奏)** | **§ 0 编辑判断** | 先判 emotion_beat / narrative_role / pacing_intent | ✅ V.2 已落 |
| **Dmytryk 七律 (#1, #7 重点)** | **§ 0 Dmytryk 第 1/7 律** | 没正向理由不切 + 内容第一 | ✅ V.2 已落 |
| BBC GEL 字数算时长 | § D 排版长度上限 | 主标题 ≤ 15 字 / pull_quote ≤ 30 字 等 | ✅ T.1 已落 |
| Refactoring UI / Carbon 色板 | § C 颜色 + § E 版式 | 每场景 ≤ 3 色 / 每场景 1 主焦点 | ✅ T.1 已落 |
| Material focused 原则 | § E 单焦点 | (隐含在 § E) | ✅ T.1 已落 |
| Kurzgesagt 故事板纪律 | § 0 + § F | "内容第一" Dmytryk #7 强化 | ✅ V.2 已落 |
| **10 个动态 PPT 套路** | **§ H 动态 PPT 套路选型** (待写) | 哪个组件用哪招 + 何时不用 bounce 等 | ⏭️ **W.5 待落** |
| **Brownie 分类 (Motion vs Fluid Typography)** | § H 同上 | 区分逐字揭示 vs 整体流动 | ⏭️ **W.5 待落** |
| **CMU Sequential Reveal 论文** | § H 同上 | SequentialWord 中文按字 80-120ms | ⏭️ **W.5 待落** |
| **Apple HIG "避免无谓动画"** | § H 同上 | 单场景套路 ≤ 2 个 | ⏭️ **W.5 待落** |
| **B 站 8-12 分钟节奏** (V.6) | **§ I 视频结构** (待写) | Hook + 6 段式 + 冷区上限 | ⏭️ **待落** |

---

## IV · 套路表 (这次调研最重要的产出)

来自 `02c-design-patterns-research.md` (V.8 第二轮):

| 套路 (英文行业名) | 中文俗称 | vocut 用在哪 | 主要参数来源 |
|---|---|---|---|
| Staggered List Reveal | 排队进场列表 | DynamicList | Material stagger 40-120ms |
| Sequential Word Reveal | 逐字逐词揭示 | DynamicQuote | CMU Sequential reveal + Brownie 分类 |
| Spotlight Cycle | 聚光循环高亮 | DynamicHighlight | Material focused 原则 |
| Number Counter | 数字滚动 | DynamicNumber | UX 标准 ease-out 800-1200ms |
| Build-Up Infographic | 累加信息图 | DynamicComparison | 通用 motion graphics |
| Trim Path Underline | 描边下划线 | DynamicHighlight 二招 | After Effects 标准 |
| Mask Sweep Reveal | 蒙版扫光揭示 | DynamicTitle | After Effects 标准 |
| Bounce-In Title | 弹跳标题 | DynamicTitle 备用 | Apple HIG spring physics |
| Cross-Fade Layer | 层叠淡入 | DynamicAtmosphere | 电影通用技法 |
| Pull-Focus Compare | 拉焦对比 | DynamicComparison 备用 | 电影镜头语言 + Material focused |

每个套路在 `components/src/patterns/` 下对应 1 个 `.tsx` 文件 (10 个文件).

---

## V · 历史调研全清单 (K-V) 状态

| 阶段 | 主题 | 调研产物 | 落地状态 |
|---|---|---|---|
| K.1-K.5 | 字体三件套 + 装饰条 + palette | tokens.ts 基础 | ✅ 全落 |
| L.1-L.4 | Open Props + tokens.ts 标尺 | tokens.ts SIZE/FONT/EASE | ✅ 全落 |
| M.1-M.3 | KeyNumber 单位去重 + burst 重设计 | 组件改写 + plan.py affinity | ✅ 全落 |
| N.1-N.3 | TYPE_RATIO 屏幕百分比字号 | tokens.ts TYPE_RATIO | ✅ 全落 |
| O.1-O.2 | Lottie 拉满画面 + LottieCard | 组件改写 | ✅ 全落 |
| P.1 | Remotion 官方模板 clone | 参考 (无代码) | ✅ 看过 |
| Q.1 | @remotion/layout-utils + captions | package.json | ✅ 装了 |
| Q.2-Q.5 | 砍 80% 装饰层 + 6 组件 mirror | (未做, 因为方向变了) | ⏸️ 悬置 |
| R.1-R.3 | 8 个设计方法论 + vocut 美学宪法 | `docs/research/methodology/*.md` 8 篇 | ✅ R.1/R.2 落, R.3 隐含进 T/U/V |
| S.1-S.5 | v0 / OpenUI / make-real / AnimateDiff 架构调研 | `docs/research/ai-design-architectures.md` | ✅ 全落 |
| T.1-T.5 | v0 prompt + palette 精简 + 视觉参考输入 + 装饰极简 + 重渲 | `plan.py` LLM_SYSTEM_PROMPT § A-G + describe_visual_reference | ✅ 全落 |
| U.1-U.4 | @remotion/transitions + 转场宪法 + 实施 | `plan.py _assign_transitions()` + `transitions-charter.md` | ✅ 全落 |
| V.1 | 抓视频编辑宪法 6 源 (Murch/Eisenstein/Dmytryk/180°/Cinemetrics/BBC) | `docs/research/methodology/editing/*.md` 6 篇 | ✅ 全落 |
| V.2 | 编辑宪法落入代码 | `plan.py` § 0 + `_apply_editing_durations` + `_cinemetrics_advisory` 等 | ✅ 全落 |
| V.3-V.5 | AutoShot / Tiger200K 数据抓取 | 数据封存 (颗粒度不对位) | ❌ 封存 |
| V.6 | 第 2 层补搜 (Video Essay) | `editing/07-bilibili-essay-pacing.md` (B 站 8-12 分钟 + huasheng 6 段式) | ⏳ **文档落了, 代码未落** |
| V.7 | 树岛坂梦日记轻度对齐 | 用户用眼对齐, 不跑数字 | ❌ 封存 (用户判断为产物) |
| V.8 第一轮 | 动态 PPT 工具调研 | `02-competitor-research-dynamic-ppt.md` (framer-motion) | ✅ **本文档同步, 开干在 W.1** |
| V.8 第二轮 | 动态 PPT 设计套路 | `02c-design-patterns-research.md` (10 套路 + 参数表) | ✅ **本文档同步, 开干在 W.5** |

---

## VI · 待落地工作清单 (W 阶段)

| Phase | 内容 | 调研落点 |
|---|---|---|
| **W.1** | 装 framer-motion + tokens.ts 加 4 个新常量块 | 类 1 + 类 2 |
| **W.2** | 写 4 个 P0 pattern (Staggered/Sequential/Spotlight/Counter) | 类 1 (framer-motion 用) + 类 2 (tokens 用) |
| **W.3** | 写 4 个 P0 Dynamic 组件 (List/Quote/Highlight/Number) | 调用 W.2 patterns |
| **W.4** | Root.tsx 注册 + VOCUT_STATIC 回退 env | (架构) |
| **W.5** | LLM_SYSTEM_PROMPT 加 § H 套路选型 + § I 视频结构 | 类 3 (10 套路 + V.6 B 站节奏) |
| **W.6** | 渲 demo, 用户看 | 验证 |
| **W.7-W.9** | 3 个 P1/P2 组件 + 6 个 P1/P2 pattern | 余下套路 |

---

## VII · 封存数据 (未来可能复用)

| 数据 | 现在不用的原因 | 未来可能用法 |
|---|---|---|
| AutoShot SHOT 200 视频 (快手娱乐) | 不对位 vocut 目标 | 如果做"快手风格" target_style 时复活 |
| Tiger200K B 站 4151 视频 (高质量短片) | 不对位 | 如果做"短片 / vlog 风格"时复活 |
| 树岛坂 BV1ScZqB8EGp 视频原文 | 用户用眼对齐 | 后续 V.10 真做实测时拿来跑 TransNetV2 |
| Manim CE | 数学题视频暂不做 | 数学题 essay 视频上线时装 |
| LottieFiles 10 万案例 | vocut Lottie 集成已够 | 想给 DynamicAtmosphere 加新模板时翻 |

---

## VIII · 给接手 Claude 的快速判断表

新对话进 vocut, 用户问"X 是什么状态" → 查这张表:

| 问题 | 答案 / 文件 |
|---|---|
| "动态 PPT 套路有哪些?" | `02c-design-patterns-research.md` (10 个) |
| "Murch 六法则在哪用了?" | `plan.py § 0 编辑判断` (V.2 落) |
| "为啥不用 Motion Canvas?" | `02-competitor-research-dynamic-ppt.md` (实测停摆 1 年) |
| "为啥 5 秒/scene 标 TODO?" | `feedback_benchmark_three_layer_order.md` (跨颗粒度编的) |
| "vocut 目标用户是谁?" | `docs/product/target-audience.md` |
| "我能改 stagger 数字吗?" | 改 `tokens.ts MOTION_STAGGER`, 全局生效 |
| "怎么回退到老组件?" | `export VOCUT_STATIC=1` |
