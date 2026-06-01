# B 站 Video Essay / 知识区节奏结构 (第 2 层补搜成果)

**抓取日期**：2026-05-29 (Phase V.6)
**用户画像**：B 站泛知识 / Commentary / 亚文化观察 + YouTube Video Essay / Edutainment
**意义**：vocut **章节级**节奏标尺。Shot 级数据需要 V.7 实测.

---

## 来源 1 · 花叔 huasheng.ai B 站科技区方法论

[https://www.huasheng.ai/insights/bilibili-video-best-practices/](https://www.huasheng.ai/insights/bilibili-video-best-practices/)

### 最优视频长度
- **5-10 分钟视频平均留存率 31.5%** (所有时长中最高)
- 科技 / 知识类 **8-15 分钟** 表现最佳
- 花叔建议初期目标 **8-12 分钟**

### 节奏结构 (秒级时间码)

| 时间段 | 该做的事 |
|---|---|
| **00:00-00:30** | Hook + 价值承诺 |
| **00:30-02:00** | 问题 / 背景设定 |
| **02:00-05:00** | 核心内容 (信息密度最高区间) |
| **05:00-06:00** | 节奏切换点 |
| **06:00-10:00** | 深入内容 / 第二高峰 |
| **10:00-12:00** | 总结 + 互动引导 |

### 章节内节奏
- **每 3-5 分钟设置一个弹幕互动点或情绪转折**
- **避免超 2 分钟的"冷区"**
- 时钟理论：爆点均匀分布整个视频

### Hook 三元素 (前 30 秒)
1. 悬念 / 痛点 / 反常识
2. 价值承诺
3. 简洁自我介绍
→ **"前 15 秒内展示价值承诺的视频，1 分钟留存率高 18%"**

### 留存基准
- YouTube 教育类平均 **42.1%** (远超 Vlog 21.5%)
- B 站科技区年观看量 240 亿次, 用户 2 亿+

---

## 来源 2 · "每周必看" 历时分析 (12725 视频 / 348 期实测)

[https://www.cnblogs.com/szdytom/p/19831471/bilibili-ugc-anal](https://www.cnblogs.com/szdytom/p/19831471/bilibili-ugc-anal)

### B 站时长演变 (6 年纵向)

| 年份 | 均值 | 中位数 |
|---|---|---|
| 2019 | 10.09 分钟 | 5.34 分钟 |
| 2025 | **19.07 分钟** | **7.95 分钟** |

→ B 站均值时长 6 年涨了 1 倍, 中位数也涨了 49%
→ **2025 中位数 7.95 分钟和花叔 8-12 推荐完全吻合**

### 时长分布
- **25% 视频仍 < 3 分钟** (短视频生态还在)
- 四分位距 / 离散系数都在涨 → 时长结构多元化

### 分区占比 ("每周必看")
- 游戏 14.55%
- 动画 12.67%
- 知识区 **8.36%**
- 其他 13.32%

→ 知识区虽然只占 8%, 但 vocut 目标用户正好在这条赛道.

---

## 来源 3 · YouTube Video Essay 学术研究 (Master Thesis)

[Recontextualized Knowledge: Available Designs of the Long-Form YouTube Video Essay](https://pdxscholar.library.pdx.edu/open_access_etds/6745/)
Michelle Lynn Arendt, Portland State University, 2024

- **分析了 7 小时 44 分钟** YouTube Video Essay 数据
- 用社会符号学多模态方法
- 主要做**叙事结构**研究, 没给 shot 级量化
- 找出"可用设计 (available designs)"：reccurring 视觉 / 语言模式
- vocut **可借鉴叙事结构**, 不能从这里拿到 ASL 数字

---

## 来源 4 · 现代电影通用 ASL 基线

[StudioBinder · How Editors Control Rhythm and Pacing](https://www.studiobinder.com/blog/how-does-an-editor-control-the-rhythm-of-a-film/)

- **现代电影 4-6 秒/shot** ≈ 观众感受的"中性节奏"基线
- 短于 4 秒 → "紧张 / 高能"
- 长于 6 秒 → "情绪沉淀"
- → vocut 编辑动作应该围绕这个 4-6 秒锚点上下浮动

---

## 副产品 · 工具

| 工具 | 出处 | 用处 |
|---|---|---|
| **TransNetV2** (ACM MM 2024) | Tiger200K 推荐 | 跑 vocut 目标 UP 视频实测 ASL |
| **ClipShots** (Github Tangshitao) | 上一轮 | YouTube + 微博 20+ 类别 shot boundary 数据 |
| **Awesome Long-Form Video Understanding** | GitHub ttengwang | 长视频研究合集, 偏 AI 任务不是创作 |

---

## 关键差距 (V.7 实测要补的)

| 颗粒度 | 现成数据 |
|---|---|
| **视频长度** | ✅ B 站 8-12 分钟 (中位 7.95) |
| **章节结构** | ✅ huasheng 6 段式 + "3-5 分钟一节" |
| **Hook 设计** | ✅ huasheng 三元素 |
| **shot 长度** | ❌ **没有 B 站 video essay 实测数据** |
| **UP 风格差异** | ❌ Contrapoints vs 沙盘上的战争 节奏差多少, 没数据 |

---

## 对 vocut 代码的修正 (硬数据落地)

### 改动 1 · 默认视频长度从 60 秒改成 8-12 分钟

`src/vocut/cli.py` 或 plan.py 应支持 `--target-minutes` 参数, 默认 10.

### 改动 2 · 章节级时间盒子

新增 `_validate_chapter_pacing(plan_items)`:
- 总时长 < 6 分钟 → warn "B 站留存最优区间 8-12 分钟"
- 总时长 > 20 分钟 → warn "超过 B 站均值 19.07 分钟"
- 任何相邻 "atmosphere/calm" 场景累计 > 2 分钟 → warn "冷区超 2 分钟, 必死"
- 第一个场景的 `narrative_role` 不是 "opening" → warn "Hook 缺失"

### 改动 3 · 修订 TARGET_AVG_SEC_BY_STYLE 注释

把 `bilibili_commentary = 5.0` 改成 `# TODO V.7: 未对照真实 B 站 video essay 实测; 临时值参考现代电影 4-6s 基线`

### 改动 4 · 改默认 style 名

`bilibili_commentary` → `bilibili_video_essay` (更准, 跟新画像对齐)

---

## 第 3 层 (实测 V.7) 该测什么

按 [docs/product/target-audience.md](../product/target-audience.md) 的 8 UP 清单, 跑 TransNetV2:

| 测什么 | 怎么用 |
|---|---|
| 每个 UP 的 ASL (平均/中位/分布) | 让用户能选 `--style=lks_subculture` 等 |
| 章节内 shot 数 (每 5 分钟切几次) | 校准 vocut 切场景的密度 |
| Hook (前 30s) 的 shot 密度 vs 中段 | 验证 huasheng "Hook 高密度"是不是真的 |
| 不同 UP 节奏方差 | 看 Contrapoints (慢) vs LKs (中) vs Folding Ideas (快) 谁更接近 vocut 用户期望 |
