# vocut 视频编辑宪法 · 抓源索引

抓取日期：2026-05-29
目的：vocut 之前**只参考了 UI 设计宪法**，没参考视频编辑自己的宪法。
"都有点快" 反馈暴露了这个缺口，所以补 6 份原典：

| # | 文件 | 作者 | 关键命题 | vocut 当前违反 |
|---|---|---|---|---|
| 01 | [murch-rule-of-six](01-murch-rule-of-six.md) | Walter Murch | 情绪 51% / 故事 23% / 节奏 10% / 视觉引导 7% / 二维 5% / 三维 4% | 只动了 15% (节奏 + 二维) |
| 02 | [eisenstein-five-montages](02-eisenstein-five-montages.md) | Sergei Eisenstein | 节拍 / 节奏 / 调性 / 泛音 / 智性 | 只做了第 1 层 (节拍均匀) |
| 03 | [dmytryk-seven-rules](03-dmytryk-seven-rules.md) | Edward Dmytryk | 7 条剪辑规则 | 违反 5 条 (尤其 #7 内容第一) |
| 04 | [180-and-30-degree-rule](04-180-and-30-degree-rule.md) | 古典好莱坞 | 轴线一致 + 角度差 ≥30° | 主体位置 / 版式变体未管控 |
| 05 | [cinemetrics-shot-length](05-cinemetrics-shot-length.md) | Cinemetrics 数据库 | 现代电影 ASL ≈ 2.5s, B 站杂谈 ≈ 5s | 3.3s/场景, 比目标用户快 1.7s |
| 06 | [bbc-on-screen-text](06-bbc-on-screen-text.md) | BBC GEL | 字幕 2-5s, 下三分之一 3-7s, 每字 0.3s | 系统性欠 2 秒 |

---

## 一句话总诊断

vocut **当前是一个"按节拍均匀切的版式动画播放器"**，
不是一个"按情绪/故事/节奏调度场景的剪辑师"。

---

## 下一步 (V.2 任务)

把这 6 份原典综合成一份 **"vocut 编辑节奏宪法"** (`docs/research/methodology/editing-charter.md`)，
落地为 4 个具体的代码改动：

1. **LLM_SYSTEM_PROMPT 重写** —— 加情绪/故事/节奏的判断指令 (Murch + Dmytryk #7)
2. **场景时长按字数 + 类型自动算** —— `_compute_min_duration_by_text` (BBC)
3. **场景总数按目标风格倒推** —— 60s 视频 ≈ 12 段 (Cinemetrics 调整)
4. **相邻场景版式差异校验** —— `_check_visual_continuity` (180° / 30° 同源)
