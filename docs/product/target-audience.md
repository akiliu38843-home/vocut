# vocut 目标用户画像

**定稿日期**：2026-05-29
**来源**：用户 (产品负责人) 2026-05-29 session 明确给出
**优先级**：**产品定义级**，所有节奏 / 视觉 / 工具决策都要回到这一页校准

---

## 一句话

vocut 不是"做杂谈"，是做**"用观点驱动的中长视频随笔"** —— B 站叫 Video Essay / Commentary / 亚文化观察，YouTube 叫 Video Essay / Edutainment。

---

## B 站视角 (中文场)

vocut 目标用户处在以下 3 个赛道的交叉点：

### 1. 泛知识 / 评论 (Infotainment / Commentary)
- **核心**：不展示生活 (vlog)，而是**"提供观点 (Take)"**
- B 站用户买单**带人格色彩的深度分析**
- 关键词："独立观点 / 深度分析 / 议题聚合"

### 2. 长视频内容矩阵 (Video Essay)
- **时长甜区**：**8-20 分钟**
- **特点**：低成本、高表达密度
- **门票**：文案 (Script) 必须有独特观点输出 → 高完播率
- **vocut 的工程位置**：服务这个 8-20 分钟黄金时长

### 3. 亚文化观察者 (Subculture Observer)
- B 站圈内称 **"亚文化杂谈"** 或 **"趋势洞察"**
- 典型题材：地雷系 / 牛郎 / 玲音 / 二次元的边缘文化
- **用户基数极其固定**、易形成私域 (圈地自萌)

---

## YouTube / 西方视角 (对应位置)

### 1. Video Essay (视频散文) ← **vocut 的最高对位**
- YouTube 最尊贵的长视频赛道
- **不是"说话"**，是剪辑 / 配乐 / 文案叙事 / 视觉排版**融为一体的艺术品**
- 头部标杆 UP：
  - [Contrapoints](https://www.youtube.com/@ContraPoints) (Natalie Wynn) — 文化批评 / 性别
  - [The Nerdwriter](https://www.youtube.com/@Nerdwriter1) (Evan Puschak) — 电影 / 文化
  - [Folding Ideas](https://www.youtube.com/@FoldingIdeas) (Dan Olson) — 互联网现象 / NFT 经典批判

### 2. Commentary Channel
- 热点 / 网络 drama / 流行文化吐槽
- 流量黑洞
- 标杆：[h3h3](https://www.youtube.com/@h3h3Productions) / [SunnyV2](https://www.youtube.com/@SunnyV2)

### 3. Edutainment (教育 + 娱乐)
- 商业化对位
- 题材深度更重：AI 技术 / 社会学现象 / 经济
- "牛郎经济" 这种**有研究深度的杂谈**会被算法归到这里

---

## 对 vocut 工程的硬约束

| 维度 | 要求 |
|---|---|
| **视频时长** | 8-20 分钟 (B 站甜区 + YouTube Video Essay 甜区) |
| **节奏** | **不像短视频 (快手 2-3s/shot)**，也不像电影 (10s+/shot)，**中间地带** |
| **视觉投入** | 不只是说话头像 + B-roll；要有"剪辑 + 排版 + 配乐"融合 |
| **观点密度** | LLM 必须能识别"独特观点 (Take)"，不是流水账 |
| **亚文化兼容** | 地雷系 / 牛郎 / 玲音 这类题材的视觉语料/字体/色彩 |

---

## V.6 实测视频抓取清单 (按这画像)

下一步做"3 层方法论第 3 层 (实测)"时, **不要只抓杂谈**, 按 3 赛道各抓 2-3 个标杆：

### B 站 (中文场)
| UP | 赛道 |
|---|---|
| **LKs 的老实人** | 亚文化杂谈 (vocut 早期参考) |
| **怪奇博物志** | 亚文化观察 |
| **沙盘上的战争** | 长视频 essay (历史) |
| **老蒋巨靠谱** | Commentary (评测/热点) |
| **(待用户补)** | 用户自己心中的标杆 |

### YouTube (英文场, Video Essay 黄金期标杆)
| Channel | 赛道 |
|---|---|
| **Contrapoints** | Video Essay 顶配 |
| **The Nerdwriter** | Video Essay 文化分析 |
| **Folding Ideas** | Video Essay + 互联网批判 |
| **h3h3 / SunnyV2** | Commentary |

---

## 这页的意义 / 该怎么用

- **任何"vocut 该多快 / 该用什么色 / 该选什么字体 / 该多长"**的决策, 都先回看这一页
- 任何"我们要 mirror 谁的剪辑风格"的提议, 都按这清单的 UP/Channel 找参考素材
- 任何"target_style" 的环境变量取值, 都应来自这清单 (e.g. `video_essay_bilibili`, `commentary_youtube`)
- 任何 "我们的用户喜欢看 X" 的假设, 都要来自这清单上的真实 UP 数据, 不是我编的
