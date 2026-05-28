# AI 设计产品调研 — 架构、Prompt、vocut 短板对照

调研对象（按学派分）：

| 学派 | 项目 | 状态 |
|---|---|---|
| **A 派 · 组件拼装** | **v0**（Vercel）| 闭源，prompt 已泄露 |
| **A 派** | **OpenUI**（W&B）| 开源 |
| **A 派** | **make-real**（tldraw）| 开源 |
| **A 派** | **Remotion 官方模板**（TikTok / Hello / Still）| 开源 |
| **B 派 · 像素生成** | AnimateDiff / Open-Sora | 开源，跟 vocut 思路相反 |

**结论先行**：vocut 站在 A 派，路子对。它的丑不是架构问题，是**LLM 提示词太短 + 没有反馈层 + 没视觉参考输入**。

---

## 1. A 派标准 7 层架构

```
1 ┃ 输入层      ── 自然语言 / 图 / 数据
2 ┃ 理解层      ── LLM 解析意图
3 ┃ 规划层      ── LLM 输出 plan
4 ┃ 组件库      ── 预制基元
5 ┃ 装配层      ── plan + 组件 → 结构
6 ┃ 渲染层      ── 出 mp4 / HTML
7 ┃ 反馈层      ── 审计 + 用户回路
```

### vocut 当前覆盖

| 层 | vocut | v0 | OpenUI | make-real |
|---|---|---|---|---|
| 1 输入 | script.md | 文本 + 图 + 文件 | 文本 + 图 | **图（wireframe）+ 文本** |
| 2 理解 | Whisper + bge embedding | LLM | LLM | LLM-vision |
| 3 规划 | LLM rerank → plan.json | TodoManager subagent | （直接渲）| （直接渲）|
| 4 组件 | 7 个 Remotion 卡片 | shadcn + Tailwind | shadcn 色板 | **无组件库**，纯 Tailwind |
| 5 装配 | render.py | LLM 直接写 React | LLM 直接写 HTML | LLM 直接写 HTML |
| 6 渲染 | Remotion → mp4 | 浏览器 React 实时 | 浏览器 HTML | 浏览器 HTML |
| 7 反馈 | **❌ 没有** | Block view + 编辑 + 部署 | 实时迭代 + action 参数 | 上下文迭代 |

---

## 2. v0 的 system prompt 深度剖析（1352 行 / 62KB）

vocut 现在的 `LLM_SYSTEM_PROMPT` 约 30 行。**差 45 倍**。

### v0 prompt 的 4 个直接对应 vocut 的章节

#### § Color System
> "ALWAYS use exactly 3-5 colors total. Count them explicitly before finalizing any design."

- 1 主色 + 2-3 中性 + 1-2 accent
- 永远 WCAG AA：正文 4.5:1，大字 3:1
- **默认不用渐变**，只在必要时用，只用类似色（蓝→青、紫→粉）
- 不混冷暖（红→青、橘→蓝是禁忌）
- 最多 2-3 色站

**vocut 现在违反**：16 套 palette 凭手感选，没强制 3-5 色上限。

#### § Typography
> "ALWAYS limit to maximum 2 font families total."

- 2 字体上限，标题 + 正文
- **明确给了 6 个场景的 Google Fonts 配对名单**：
  - 现代/科技：Space Grotesk Bold + DM Sans Regular
  - 编辑/内容：Playfair Display Bold + Source Sans Pro Regular
  - 大胆/冲击：Montserrat Black + Open Sans Regular
  - 优雅/高端：Playfair Display SemiBold + DM Sans Light
  - 干净/极简：DM Sans Bold + DM Sans Regular
  - 企业/专业：Work Sans Bold + Open Sans Regular
- line-height: **1.4-1.6**（用 Tailwind `leading-relaxed` 或 `leading-6`）
- 字号阶梯：text-sm → base → lg → xl → 2xl
- **body 最小 14px**（text-sm），低于此一律不行
- 装饰字体不能用于正文

**vocut 现在违反**：自己选了思源黑+IBM Plex（OK），但**没绑死场景**——editorial 用啥、anime 用啥没钉。

#### § Layout Structure
> "ALWAYS design mobile-first."

- 320px 起始，添 768 → 1024+
- 间距系统：section 间距 `space-4`(16px) 最小，相关元素 `space-2`(8px)
- **每个 section 只能一种对齐方式**（左/中/右选一个）
- 不可混对齐

**vocut 现在违反**：组件之间对齐不一致（有的居中有的左对齐）。

#### § Creative Decision Framework
**最金条**：

> 模糊请求（"现代/简洁"）→ **BE BOLD**：用意外的颜色组合、独特版式
> 有品牌指引 → **BE RESPECTFUL**：在框架内执行
> 企业 App → **BE CONSERVATIVE**：习惯模式
> 个人/创意项目 → **BE EXPERIMENTAL**：非常规版式

**Final Rule**: "Ship something interesting rather than boring, but never ugly."

**vocut 现在没有**：没有"判断"逻辑，所有视频走一样的风格分配。

---

## 3. make-real 的"视觉参考输入"模式

3 个 LLM 各一份 prompt（Anthropic / OpenAI / Google），核心机制：

1. **输入是 wireframe（用户画的图）+ 上下文文字**
2. **红色 = 注释，从结果里排除**（聪明的约定）
3. **"宁可猜，也别留空"**："favor completeness over perfection"
4. **支持上下文迭代**：传入上一版的 iframe 代码 → 在它上面加

**vocut 没有的关键点**：
- ❌ 没办法把"参考截图"作为输入
- ❌ 没有"上一版 → 改进"的迭代机制
- ❌ 没有"宁猜不空"的兜底规则

---

## 4. OpenUI 的简化路线

**反过来看**：OpenUI 的 system prompt 才 50 行左右，比 v0 短 95%。

它的策略：
- **靠 shadcn 的设计 token**做约束（--background / --foreground / --primary / --accent / --muted 这些）
- 让 LLM 直接写 Tailwind，**没有自己的组件库**
- 用户可以**自定义 system prompt + temperature + model**
- 简单暴力，但**靠 shadcn 站台**保住底色

vocut 跟 OpenUI 的差异：
- vocut 有组件库（Remotion 卡片）但**没用 shadcn 那种语义 color token**
- vocut 的 system prompt 既不像 v0 那么细，也不像 OpenUI 那么靠成熟设计系统兜底
- vocut **两头不靠**

---

## 5. Remotion 官方模板（前面调研过）

3 个模板共同特征：
- **一帧 1-2 个元素**
- **WebKit text-stroke 20px**（TikTok 模板里的关键技巧）
- spring 一种动效，不多种
- **fitText() 自动适配**字号

vocut 学会了字号自适应（部分），其他大部分没学。

---

## 6. B 派对照：AnimateDiff / Open-Sora

像素生成派的思路：
1. 文字 → CLIP / T5 编码
2. 进 diffusion model
3. 多帧之间用 motion module 保证一致性
4. 解码出像素

**vocut 庆幸自己不是这条路**：
- 不需要 GPU
- 不需要训练数据
- 可控、可调试、可解释
- 输出**确定性**（同 plan → 同 mp4）

像素派的痛苦：渲染失败没法 debug，"长得不对"没办法精确改，每次都是抽奖。

---

## 7. vocut 短板清单（按改造性价比）

| # | 短板 | 改造 |
|---|---|---|
| 1 | **LLM_SYSTEM_PROMPT 只 30 行** | 抄 v0 的 4 个设计章节进来，加到 1000+ 行 |
| 2 | **没视觉参考输入** | 学 make-real，让用户传"想做成 X 那样"的截图 |
| 3 | **没反馈层 / 不能迭代** | 学 v0 的 action 参数，支持"在 plan.json 上改" |
| 4 | **palette 16 套手感选** | 抄 v0 的 3-5 色硬规则 + WCAG 强制 |
| 5 | **字体没绑场景** | 抄 v0 的 6 配对名单 |
| 6 | **对齐混乱** | 强制每 scene 1 种对齐 |
| 7 | **没 Creative Decision Framework** | 加 4 类风格判断逻辑 |
| 8 | **组件之间没语义 color token** | 学 OpenUI/shadcn：bg / surface / fg / accent / muted / border 这种命名 |

---

## 8. vocut 下一步路线图（按这次调研建议）

```
现在 ─── 抓素材结束 ─── ↓

[第 1 步] 把 v0 prompt 的 4 个设计章节翻译成中文，
         做 vocut 新版 LLM_SYSTEM_PROMPT
         （从 30 行 → 600 行，能塞 50 倍信息）

[第 2 步] palette 从 16 套砍到 6 套
         每套都用 v0 的"3-5 色"规则强制审查

[第 3 步] 字体绑死 v0 的 "Editorial / Bold / Clean" 3 个配对

[第 4 步] 砍 80% 装饰层（CardBackground / SceneFrame / AccentFx 全删）
         组件极简化 mirror Remotion 官方模板

[第 5 步] 加反馈层：
         - 渲染后自动检查 palette / 字号 / 对齐是否违宪
         - 输出违反清单到 plan.json.review

[第 6 步] 加视觉参考输入：
         vocut plan --reference ./inspiration.png
         → vision LLM 描述参考图风格 → 注入 prompt
```

---

## 9. 一句话总结

vocut **不需要换架构**（A 派对的）。它需要：
1. **更长 / 更细的 LLM prompt**（学 v0）
2. **更少 / 更被强制的设计元素**（学 Remotion 模板 + shadcn）
3. **反馈回路**（学 v0 的 action / OpenUI 的迭代）
4. **视觉参考输入**（学 make-real）

这 4 件做完，vocut 就从"程序员做出来的"变成"AI 设计产品"了。

---

参考素材：
- v0 prompt: [docs/research/methodology/ai-prompts/v0-2025-07-20.md](methodology/ai-prompts/v0-2025-07-20.md) (1352 行)
- make-real 源码: `/tmp/design-refs/make-real/`
- OpenUI 源码: `/tmp/design-refs/openui/`
- Remotion templates: `/tmp/design-refs/template-{tiktok,helloworld,still}/`
