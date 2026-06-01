# vocut 动态 PPT 方法论 6 步

> **2026-05-29** · 从 V.8 三轮调研 + W.1-6 + X.4 一系列翻车里提炼
> 跨 session 永久可读. 接手 vocut 的任何 Claude 必读.
> 配套全局 6 条 feedback memory (家目录), 任何项目都能用.

---

## 一句话

**不要在抽象层做事**. 6 步全部都是"对照实物 / 先看再想 / 立刻自审"。

---

## 6 步硬流程 (任何动态 PPT 类任务都走)

```
1. 形式枚举      列 ≥ 10 种动态 PPT 形式 (不许漏)
2. 锁标杆 UP    1-3 个真 video essay, 标 3-5 个段落 "这是哪种形式"
3. 排优先级     按"用户感官目标" 排 P0/P1/P2 (不按实现难度!)
4. 5 层防御     每种 P0 形式独立: 工具 / 套路 / 数据 / 大厂规范 / 学术
5. 小 spike    新依赖前 30 分钟最小 demo 在 Remotion 跑通
6. 渲一帧自审   每写完一个组件立刻渲 + 抽帧 + Read 自看
```

---

## 6 步详细 + 历史踩坑

### 第 1 步 · 形式枚举 (≥ 10 种)

入场第一步, 列动态 PPT 所有形式 (中英 + 跨域):

```
1. 入场动画        Stagger / Sequential       Material Design 3 stagger 40-120ms
2. 持续累积        Build-Up Infographic      Vox / Kurzgesagt 经典招
3. 数据图表 morph  Vizzu / ECharts           柱图 → 饼图 → 线图 自动过渡
4. 滚动叙事        Scrollytelling             NYTimes Snow Fall (2012)
5. 思维导图        Mind Map / Concept Map    React Flow / mermaid
6. 3D 场景累加     R3F / Three.js            Vox 地球+城市标签
7. 手绘白板        Excalidraw / tldraw       视觉风格特殊
8. 视频特效        transitions / shaders     Remotion transitions
9. 概念地图        knowledge graph           D3 force-directed
10. 拼贴 / collage  静态切换                  抒情场景
```

**历史踩坑**: vocut 第 1 轮调研只查了"入场动画" 工具, 漏 BuildUp; 第 2 轮 10 套路里漏思维导图; 第 3 轮列 5 子赛道又漏思维导图. **3 次都因为入场没列完**.

→ **不列完不许进 5 层防御**.

---

### 第 2 步 · 锁标杆 UP + 标段落

挑 1-3 个 vocut 目标用户 (B 站 video essay / YouTube Video Essay):

- 树岛坂 (B 站, 5w 粉, 哲学杂谈)
- Folding Ideas (YouTube, 互联网批判)
- Nerdwriter / Contrapoints (YouTube Video Essay 顶配)

操作:
1. yt-dlp 拉 1-2 支视频
2. 暂停 + 标 3-5 个段落: "00:32-00:45 是 BuildUp / 02:10-02:25 是思维导图 / 04:30-04:45 是数据图表"
3. 落到 `docs/research/methodology/reference-segments/<up>-<bvid>.md`

**历史踩坑**: vocut 全程没真看一次树岛坂梦日记, 反复跑偏被用户判否. 用户提了 4 次"看树岛坂" 我都推后查资料.

→ **不看真视频不许写代码**.

---

### 第 3 步 · 排优先级 (用户感官 first)

P0 不是"最好做的", 是"用户看完第一句会说啥 → 最对位目标的"

错误优先级 (按实现难度):
- P0 = 入场动画 (好做)
- P1 = BuildUp (难)

→ 用户看完第一句: "这不是动态 PPT, 还是字卡一闪"

正确优先级 (按感官目标):
- P0 = BuildUp / 思维导图 / 图表 morph (用户看完: "哇, 这是 video essay 那种感觉!")
- P1 = 入场动画 (基础底层, 但单独看不像 PPT)

**历史踩坑**: V.8 第 2 轮 P0 选错, W.1-6 6 小时全跑废.

---

### 第 4 步 · 每种 P0 形式 5 层防御

每种 P0 形式独立调研 (5 层):

| 层 | 内容 | 工具 |
|---|---|---|
| L1 | 关键词扩展 (≥ 10 个) | LLM 自己想 |
| L2 | GitHub search (≥ 6 query) | `fetch_metrics.py search` |
| L3 | GitHub topic 搜 (≥ 3 个 topic) | 同上 |
| L4 | Awesome list 挖 (≥ 5 个) | `fetch_metrics.py find-awesome` |
| L5 | 头部仓 README mine-similar | `fetch_metrics.py mine-similar` |

**必跑 sanity gate 4 问**:
- Q1: 星数最高的差距 > 5×? 中间档漏了?
- Q2: 不同 query 重合 > 80%? 关键词不够发散
- Q3: ≥ 5k★ 都符合主题?
- Q4: 地理特异? 漏了某国语言

---

### 第 5 步 · 小 spike (30 分钟)

任何新依赖 (`bun add X`), 装上后**第一件事**:

```
1. 写最小 demo (3-5 行核心 API 调用)
2. 在 Remotion 跑一次 npx remotion render
3. 抽一帧看
4. 工作 → 进 production 代码
5. 不工作 → 立刻换 (不要 reason 半小时)
```

**历史踩坑**: X.4 React Flow 写完 150 行才渲, 黑屏. 浪费 1 小时. 应该装上后立刻 3 节点 demo, 5 分钟发现 SSR 不兼容 + 换 SVG.

---

### 第 6 步 · 渲一帧自审

落代码后**立刻**渲一帧 + Read 自看, 检查 3 件:

| 维度 | 标准 (720p @ 1280×720) |
|---|---|
| **字号** | 中文 ≥ 25px (3.5% 屏高), 英文 ≥ 18px |
| **配色** | 同色谱 (mixHex) 或邻近色, 不要 3 种跨色 |
| **布局** | 元素全在屏内, 没溢出 / 重叠 |

不对 → 自己改 → 再渲 → 至少 2 轮 → 觉得过关再给用户看.

**历史踩坑**: X.4 v2 字号 18px / v4 橘+白+黑 三色冲突, 都是没自审 → 用户判否 → 再改 → 浪费时间.

---

## vocut 已踩过的 8 次坑 (历史回放)

| 时间 | 阶段 | 错误 | 该用哪一步预防? |
|---|---|---|---|
| 2026-05-29 | V.8 R1 | 推 Motion Canvas (已死 1 年) | 第 4 步 sanity gate (维护强度) |
| 2026-05-29 | V.8 R2 P0 | 入场动画 P0, BuildUp P1 | **第 3 步** (用户感官 first) |
| 2026-05-29 | W.1-6 | 6 小时落 4 字卡组件 | 第 3 步 (跟错 P0) |
| 2026-05-29 | V.8 R3 | 列 5 子赛道漏思维导图 | **第 1 步** (形式枚举) |
| 2026-05-29 | X.4 v1 | React Flow 直接写 → 黑屏 | **第 5 步** (spike) |
| 2026-05-29 | X.4 v2-v3 | 边标签 18px 太小 | **第 6 步** (字号自审) |
| 2026-05-29 | X.4 v4 | 橘+白+黑 配色冲突 | **第 6 步** (配色自审) |
| (整个过程) | - | 没真看一次树岛坂梦日记 | **第 2 步** (锁标杆) |

→ **每次坑都对应"省略了某一步"**, 不是新错.

---

## 配套全局 memory (家目录)

每个根因独立成全局 feedback (跨项目, 不只 vocut):

| 全局 memory | 解药 |
|---|---|
| [feedback-user-sensory-first](~/.claude/projects/-Users-a26976/memory/feedback_user_sensory_first.md) | 第 3 步 |
| [feedback-enumerate-forms-first](~/.claude/projects/-Users-a26976/memory/feedback_enumerate_forms_first.md) | 第 1 步 |
| [feedback-spike-before-invest](~/.claude/projects/-Users-a26976/memory/feedback_spike_before_invest.md) | 第 5 步 |
| [feedback-look-real-artifact-first](~/.claude/projects/-Users-a26976/memory/feedback_look_real_artifact_first.md) | 第 2 步 |
| [feedback-render-inspect-each-step](~/.claude/projects/-Users-a26976/memory/feedback_render_inspect_each_step.md) | 第 6 步 |
| [feedback-color-harmony-rule](~/.claude/projects/-Users-a26976/memory/feedback_color_harmony_rule.md) | 第 6 步 (配色专项) |

vocut 项目级文档 = **6 步流程的具体落地**
全局 memory = **6 条解药跨项目通用**

---

## 接手 vocut 的人, 必读顺序

1. `CLAUDE.md` (项目根目录) — 总览
2. `docs/product/target-audience.md` — vocut 目标用户画像
3. **这页** — 6 步硬流程
4. `docs/research/methodology/research-to-code-map.md` — 调研 → 代码 映射
5. `docs/research/methodology/editing-charter-applied.md` — Murch / Dmytryk 落点
6. 任何具体调研的 02-/03-/00- 系列 (按需)
