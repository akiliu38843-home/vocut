# vocut 编辑宪法 · 落入代码改动清单

落地日期：2026-05-29
对应任务：Phase V.2
依据：`docs/research/methodology/editing/*.md` (6 份原典)

---

## 一句话：vocut 从"按节拍器均匀切"升级成"按情绪/故事/节奏调度"

---

## 改动 1 · LLM 必须先做编辑判断 (Murch 84% 权重)

**位置**：`src/vocut/plan.py` LLM_SYSTEM_PROMPT 顶部新增 § 0

LLM 现在必须为每一句话先给 3 个判断 (在选组件之前)：

| 字段 | 取值 | 含义 |
|---|---|---|
| `emotion_beat` | hook / tension / calm / release / punch | 这一段观众的情绪是什么 (51% 权重) |
| `narrative_role` | opening / evidence / claim / example / atmosphere / closing | 这一段在剧本的哪个功能位 (23%) |
| `pacing_intent` | fast / medium / slow | 这一段该快还是慢 (10%) |

**Dmytryk 第 7 律"内容第一"**：先想清楚这段在干嘛，**再**选组件。
**Dmytryk 第 1 律"无正向理由不切"**：相邻同功能句子建议在 reasoning 里写"建议合并"。

`RERANK_TOOL` 把这 3 个字段加成 required，LLM 不给就走默认 (calm/evidence/medium)。

---

## 改动 2 · 按字数 + 类型 + 情绪算时长 (BBC + Cinemetrics)

**新增函数**：`_apply_editing_durations(plan_items)` (在 `_assign_transitions` 之前跑)

每个 motion_graphic 场景的时长按 **max(BBC 字数底线, 组件基线 × pacing 系数)** 计算：

### 组件基线 (Cinemetrics B 站杂谈基准 ≈ 5s/scene)

| 组件 | 基线 | 理由 |
|---|---|---|
| title_card | 5.0s | 章节给观众喘息 |
| pull_quote | 4.5s | 引言留时间读 |
| key_number | 2.8s | 数字一眼看完 |
| comparison_panel | 6.0s | 对比要时间扫两边 |
| list_item | 4.0s + 每项 0.5s | BBC 阅读速度 |
| keyword_highlight | 3.0s | 单关键词 |
| lottie | 3.5s | 氛围动效 |

### pacing 倍率

| LLM 给的 pacing_intent | × 倍率 |
|---|---|
| fast | 0.7 |
| medium | 1.0 |
| slow | 1.4 |

### BBC 字数底线 (硬下限)

- 中文字符 × 0.30s
- 英文/数字 × 0.12s
- 加总 ≥ 2.0s (BBC 字幕最短停留)

### 总封顶 / 兜底

`min(8.0s, max(2.0s, 计算值))` —— 防极端短/长。

---

## 改动 3 · Cinemetrics 节奏体检 (advisory 不阻塞)

**新增函数**：`_cinemetrics_advisory(plan_items, target_style)`

读 env `VOCUT_TARGET_VIDEO_STYLE` (默认 `bilibili_commentary` → 5s/scene 基准)，比较实际平均场景秒数 vs 目标基准。

| target_style | target_avg_sec |
|---|---|
| tiktok | 2.5 |
| **bilibili_commentary** (默认) | **5.0** |
| edu_explainer | 8.0 |
| documentary | 12.0 |

如果偏离目标 ±20% 以上，打印 stderr warning：
```
⚠ pace_advisory: avg 2.07s/scene vs target 5.0s (+58.7%).
  Cinemetrics suggests ~7 scenes for this video length (you have 18).
```
不阻塞 plan 产出，只提醒。完整结果写进 `plan.json → meta.pace_advisory`。

---

## 改动 4 · 连续相似场景告警 (30° 律的 vocut 翻译)

**新增函数**：`_check_visual_continuity(plan_items)`

扫一遍相邻场景，如果：
- 同一个组件 (e.g. 连续 2 个 key_number)
- 同一个 palette
- 同一个 bg_style

→ 报为 `jump_cut`。也算同 palette 连续运行的最长段。

写入 `plan.json → meta.continuity_advisory`，stderr 打印总数。

---

## 改动 5 · render.py 不需要改

render.py 里已经有 `duration_scale = vo_dur / total_planned` —— 这会把所有场景**等比例**压缩到旁白时长。

所以这次改动的真正价值是**相对节奏差异**：
- 旧版：所有 motion_graphic 都用 `card_duration_sec` 齐刷刷，缩完一样长
- 新版：title_card 7s / key_number 2s 的 **3.5 倍差异**会保留下来 (按比例都缩成 1.4x 短)

**这才是治"都有点快"的核心** —— 观众感受到的"快"是均质感，而不是绝对秒数。

---

## 自测结果

```
模拟 18 场景全 fast (老 vocut 节奏):
  avg = 2.07s, ok=False, delta=+58.7%
  → "Cinemetrics suggests ~7 scenes for this video length (you have 18)"

模拟 4 场景混合 pacing (新 vocut 应有节奏):
  title_card  slow   → 7.0s   (5.0 baseline × 1.4)
  key_number  fast   → 2.0s   (2.8 × 0.7 触底到 BBC 2.0)
  pull_quote  slow   → 6.3s   (4.5 × 1.4, BBC 字数 5.58 输给 baseline)
  keyword     medium → 3.0s   (3.0 × 1.0)
  avg = 4.58s/scene, ok=True (delta 8.5% 在容差内)
```

→ 新版有显著的节奏差异，老版没有。

---

## 用户操作

无 CLI 改动。下次 `vocut plan` 就生效。如果想换目标风格：

```bash
export VOCUT_TARGET_VIDEO_STYLE=edu_explainer   # 慢一点 (8s/scene)
export VOCUT_TARGET_VIDEO_STYLE=tiktok          # 快 (2.5s/scene)
```

---

## 尚未做的事 (留给 V.3+)

1. **真正缩短场景数**：当前 advisory 只报警不动手。要真合并需要再调 LLM 让它输出 "建议合并到 scene N"，目前只在 reasoning 里 freeform 提示。
2. **Eisenstein 调性蒙太奇**：按情绪相册重排场景顺序，当前是按剧本顺序播。
3. **180° 主体位置一致性**：要等组件支持 alignment 变体字段才能做。
