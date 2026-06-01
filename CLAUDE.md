# vocut — 给接手 Claude 的方向指南

## 必读: 目标用户画像

**任何**节奏/视觉/工具决策前, 先看 [docs/product/target-audience.md](docs/product/target-audience.md).

一句话: vocut 是给 **B 站 Video Essay / 评论 / 亚文化观察** 和 **YouTube Video Essay / Commentary / Edutainment** 创作者用的, **8-20 分钟中长视频**. 不是短视频(快手类), 也不是电影解说.

## 找数字的 3 层方法论 (硬规则)

任何要在代码里硬编码一个数字 (阈值/默认/baseline) 前, **严格按顺序**:

1. **宪法层** — 原典 (Murch / Eisenstein / Dmytryk / BBC GEL) → 思想框架
2. **现成层** — 开源 repo / 数据集 / ML 模型 (AutoShot / Tiger200K / TransNetV2 / PapersWithCode)
3. **实测层** — 抓真实目标用户视频测

**不许跳第 2 层凭空编**. 2026-05-29 编 `bilibili_commentary = 5.0s/scene` 翻车过. 看 [docs/research/methodology/editing/](docs/research/methodology/editing/) 和 [docs/research/methodology/editing-charter-applied.md](docs/research/methodology/editing-charter-applied.md).

## 用户沟通风格

- 用户是非技术产品负责人 → **大白话 + 生活类比, 不堆术语**
- 写完文件附 `o <绝对路径>` 让用户复制打开, **不要**自己跑 `open`
- 汇报数字前先讲方法 + 含义 + 数据源 + 假设

## 已落地的关键宪法 (历史)

- [editing-charter-applied.md](docs/research/methodology/editing-charter-applied.md) — V.2 落到 `src/vocut/plan.py` 的 Murch / Eisenstein / Dmytryk / BBC / Cinemetrics 5 套规则
- [transitions-charter.md](docs/research/methodology/transitions-charter.md) — 转场宪法
- [00-design-charter.md](docs/research/methodology/00-design-charter.md) — 视觉设计宪法
