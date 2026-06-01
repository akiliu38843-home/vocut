# Cinemetrics · 平均镜头时长 (ASL) 数据库

**来源**：cinemetrics.uchicago.edu (芝加哥大学维护的全球电影 ASL 众包数据库)
**参考链接**：
- [Cinemetrics Database · MetaFilter](https://www.metafilter.com/90102/Cinemetrics-database-of-Average-Shot-Length)
- [Filmmakers Academy · ASL Glossary](https://www.filmmakersacademy.com/glossary/average-shot-length-asl/)
- [PMC · Quicker, faster, darker: Changes in Hollywood film over 75 years](https://pmc.ncbi.nlm.nih.gov/articles/PMC3485803/)
- [ResearchGate · ASL 1903-2006](https://www.researchgate.net/figure/Average-shot-length-of-films-in-seconds-from-1903-2006-arranged-by-year-The-total_fig1_236630040)

---

## 一句话总结

**电影行业 100 年来"平均一个镜头几秒"的演化数据，是判断节奏的客观标尺。**

---

## 核心数据 (英语片 ASL 演化)

| 年代 | ASL (秒) | 备注 |
|---|---|---|
| 1900-1920 (默片初期) | 35+ | 一个镜头能放半分钟 |
| 1930s (有声片诞生) | 12 | 因为对白拉长镜头 |
| 1960 前 | 8-11 | 黄金时代标准 |
| 1980-2000 | 4-6 | 加速 |
| 2000-今 | **2.5** | "短切时代" |
| 极端案例 | 2.4 | 《谍影重重 2》(动作片下限) |

→ **现代主流好莱坞电影约 2.5 秒/镜头**

---

## 但是 ⚠️ —— vocut 不是电影

电影 ASL 数据是**"一个 shot"** (一个镜头) 的时长，**不是 "一个场景"** 的时长。
电影里一个"场景"通常包含 5-20 个 shot。

vocut 的"scene" ≈ 电影的"sequence" (一组镜头讲一件事)，**不能直接对比 2.5 秒**。

---

## 对 vocut 真正能借鉴的数据

### 对标 B 站杂谈视频的真实节奏

下面的数字是行业经验值 (vocut 后续需要实际扫一批参考视频确认)：

| 视频类型 | 典型场景时长 | 典型说话节奏 |
|---|---|---|
| 短视频 (抖音 / TikTok) | 1.5-3 秒 | 250+ 字/分钟 |
| B 站杂谈 (LKs / 怪奇博物志) | **4-8 秒** | 200-250 字/分钟 |
| 知识科普 (回形针 / 老高) | **6-12 秒** | 180-220 字/分钟 |
| 长视频解说 (沙盘上的战争) | 10-20 秒 | 160-200 字/分钟 |
| 纪录片 (BBC / Netflix) | 8-15 秒 | 140-180 字/分钟 |

### vocut 当前的位置

- 18 场景 / 60 秒 = **3.3 秒/场景**
- 这个值**夹在抖音和 B 站杂谈之间**
- 但 vocut 目标用户是 **B 站杂谈 / 二次元解说**

→ **vocut 应该把平均场景时长拉到 4-6 秒，目前 3.3 秒确实偏快。**

---

## 推论：vocut 60 秒视频的健康场景数

| 目标节奏 | 平均场景秒 | 60 秒视频场景数 |
|---|---|---|
| 短视频感 | 2.5s | 24 段 (太碎) |
| **B 站杂谈感** | **5s** | **12 段** ← 推荐 |
| 知识科普感 | 8s | 7-8 段 |
| 纪录片感 | 12s | 5 段 |

→ vocut 当前 18 段 / 60 秒应该收敛到 **10-12 段 / 60 秒**

---

## 对 vocut 的转化

**新增 plan.py 规则**：

1. `_assign_durations(plan_items, target_video_seconds, target_style)`
   - `target_style="bilibili_commentary"` → 平均 5s/场景
   - 总场景数 = `target_video_seconds / 5`
2. **场景类型差异化**：
   - title_card: 5-7s (慢)
   - pull_quote: 4-5s (中)
   - key_number: 2-3s (快, 数字看一眼就够)
   - lottie: 3-4s
   - comparison_panel: 6-8s (要对比要时间)
3. 在 LLM rerank 阶段加约束：**总时长 / 场景数 ≥ 4s**，否则要求 LLM 合并相邻场景
