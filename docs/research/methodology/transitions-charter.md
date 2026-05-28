# vocut 转场设计宪法

参考来源：
- **@remotion/transitions**（Remotion 官方，18 个 presentations）
- **Adobe Premiere 编辑师共识**（"perfect transition is unnoticed"）
- **Disney 12 Animation Principles**（slow in/out、timing、spacing、staging）
- **Material 3 transitions**（fade through、shared axis 等命名）

---

## §1 核心理念

> **"The perfect transition goes completely unnoticed by your audience."** — Adobe editor's craft consensus

转场是**为内容服务的**，不是为转场服务。3 条铁律：

1. **不抢戏**：观众应该几乎注意不到转场存在
2. **一致性 > 多样性**：整支视频转场风格保持一致，不要每段换一种
3. **匹配情绪**：能量场景用硬切 / 慢叙述用 dissolve / 章节转换用 dip-to-black

---

## §2 vocut 允许使用的转场（按"专业到业余"排序）

@remotion/transitions 提供 18 种 presentations。**vocut 只用前 4 种，其他 14 种禁用**。

### ✅ 允许（4 种）

| Remotion 名 | 中文 | 用场 | 时长 |
|---|---|---|---|
| `none` | 硬切 | 节奏快的句子衔接、信息密集场景 | 0 帧 |
| `fade` | 淡入淡出 | 默认转场，95% 的场景用它 | **15-20 帧** (0.5-0.67s) |
| `slide` | 滑动 | 章节切换 / 主题转移 | **20-30 帧** (0.67-1.0s) |
| `dissolve`(=fade 一种变体) | 交叉叠化 | 跟 fade 类似，更柔 | 15-20 帧 |

### ❌ 禁用（14 种）—— 一律不出现在 vocut 自动分配里

| 禁用 | 为啥 |
|---|---|
| `book-flip` / `flip` | PPT 翻页感，业余 |
| `iris` | 卡通 / 老电视感 |
| `clock-wipe` | 模板风，廉价 |
| `crosswarp` / `cross-zoom` / `dreamy-zoom` / `zoom-blur` / `zoom-in-out` | 抢戏，让观众注意转场而不是内容 |
| `linear-blur` | 抖音特效感，跟 editorial 不搭 |
| `ripple` | 卡通水波感 |
| `swap` | 像 PPT 切片动作 |
| `wipe` | 80 年代电视新闻感 |
| `film-burn` | 复古做作 |

**这 14 种代码仍在 @remotion/transitions 包里**（素材库不删），但 vocut 默认不选。

---

## §3 时长（Disney + Atlassian + Apple HIG 综合）

转场时长来自 3 个标尺的共识区间：

| 类型 | vocut 时长 | 依据 |
|---|---|---|
| 硬切 `none` | 0 帧 | 不需要时长 |
| fade（场景内衔接）| **15-20 帧 / 0.5-0.67s** | Atlassian "transitions 150-400ms" 的视频版翻倍（视频比 UI 慢一倍） |
| slide（章节切换）| **20-30 帧 / 0.67-1.0s** | Disney "slow in slow out" + 留时间让观众接受新场景 |
| dip-to-black（开场/结尾）| **30-45 帧 / 1.0-1.5s** | Hollywood 行业标准 |

**禁止区**：
- 单个转场 < 8 帧（观众看不见）
- 单个转场 > 60 帧（停太久）

---

## §4 缓动曲线（Disney "slow in / slow out"）

vocut 默认全部用 `springTiming({damping: 200})`：
- 起步慢 → 中间快 → 结束慢
- 对应 Disney 第 5 原则的工程实现
- @remotion/transitions 自带

**不用 `linearTiming`**（除非"信息切换"场景，比如统计数字翻牌）

---

## §5 vocut 转场 vs 组件的关系

转场不是组件的一部分，是**两个组件之间**的事。架构：

```
plan.json
  scene[0]: KeyNumber             ┐
                                  │ ← transition_to_next: "fade", 18 frames
  scene[1]: PullQuote             ┤
                                  │ ← transition_to_next: "slide", 24 frames
  scene[2]: TitleCard             ┘
```

`plan.py` 的 `_assign_motion_styles` 之后多跑一遍 `_assign_transitions(plan_items)`，
给每个 scene 加 `transition_to_next` 字段（最后一个 scene 不加）。

---

## §6 vocut 转场自动分配规则

按 scene 类型 + 章节切换判断：

```
if 当前 scene == title_card (章节卡):
    → transition_to_next = "slide" (章节切换感)
elif 下一段 scene == title_card:
    → transition_to_next = "dip-to-black" 等价 (或 slide)
elif 当前段是 lottie:
    → transition_to_next = "fade" (温柔过渡)
elif 当前段是 footage 且下段也是 footage (同主题延续):
    → transition_to_next = "none" (硬切，保持节奏)
elif 两段类型差异大 (footage → motion_graphic):
    → transition_to_next = "fade"
else:
    → transition_to_next = "fade" (默认)
```

**一致性约束**：整支视频里 `slide` 总次数 ≤ 章节数；
`none` 总次数 ≤ 视频总场景数的 30%（避免太碎）。

---

## §7 反则（绝对不允许）

❌ 同一支视频用超过 3 种转场（一致性原则）
❌ 单个转场 > 1.5 秒（观众等不及）
❌ 转场+大动效组件入场叠加（让观众一次接收两个事件）
❌ 用 zoom-blur / dreamy-zoom / film-burn 这种"看一眼就感觉廉价"的 14 种
❌ 章节卡前后用硬切（章节断开要给观众喘息）

---

## §8 实现路径（U.4 任务）

1. 装 `@remotion/transitions` 进 `components/`
2. `Card.tsx` 不变，**新加** `Scenes.tsx`：用 `<TransitionSeries>` 包多段 `<TransitionSeries.Sequence>` + 中间夹 `<TransitionSeries.Transition>`
3. `render.py` 改造：原本是 `concat_segments` 拼 mp4，现在改用 Remotion 一次性渲染整条 TransitionSeries（Remotion 处理转场）
4. `plan.py` 加 `_assign_transitions(plan_items)`，给每段写 `transition_to_next`

**素材库零改**：所有 7 个组件代码不动；只是它们之间多了 `<Transition>` 节点。
