# BBC · 屏上文字停留时长标准

**来源**：BBC Subtitle Guidelines (subtitleguidelines.bbc.co.uk)
**作者身份**：英国国家电视台，全球字幕/lower third 行业标杆
**参考链接**：
- [Clevercast · BBC Subtitling Guidelines](https://www.clevercast.com/bbc-subtitling-guidelines/)
- [SubHero · Subtitle Standards Compared (Netflix/BBC/Amazon)](https://subhero.io/blog/subtitle-standards-guide)
- [PMC · Viewers can keep up with fast subtitles: Eye movement evidence](https://pmc.ncbi.nlm.nih.gov/articles/PMC6007935/)
- [Riverside · Lower Third Guide](https://riverside.com/video-editor/video-editing-glossary/lower-third)

---

## 一句话总结

**字幕停 2-5 秒、下三分之一信息卡停 3-7 秒，才够观众看完。**

---

## 核心数字 (BBC 官方)

### 字幕 (Subtitle)

- **停留时长**：2-5 秒
- **最小停留**：0.3 秒/字 (英文)
  - 4 字幕 → 至少 1.2 秒
  - 8 字幕 → 至少 2.4 秒
- **阅读速度**：160-180 字/分钟 (英文)
- **行数上限**：通常 2 行，最多 3 行 (当 lower third 同时存在时)

### 下三分之一信息卡 (Lower Third)

- **停留时长**：**3-7 秒** (人名 / 数据 / 来源标注的标准窗口)
- **大于 7 秒**：观众已经记完了，浪费时间
- **小于 3 秒**：观众根本看不完

---

## 中文场景的换算 (vocut 关心的)

中文字符密度大约是英文的 2-3 倍 (一个汉字 ≈ 2 个英文字符的信息量)：

| 屏上文字量 (中文) | 最小停留 | BBC 风格停留 |
|---|---|---|
| 6 字 (短标题) | 1.5s | 3s |
| 12 字 (一句话) | 2.5s | 4s |
| 20 字 (引言) | 4s | 5-6s |
| 30 字 (段落) | 5.5s | 7s |
| 40+ 字 | 7s+ | 8-10s |

经验公式 (vocut 用)：

```
最小停留秒数 = max(2, 中文字数 × 0.2)
舒适停留秒数 = max(3, 中文字数 × 0.3)
```

---

## 对 vocut 的拷问

vocut 当前的"刺啦看不清"问题：

| 当前 vocut 行为 | BBC 标准 | 差距 |
|---|---|---|
| PullQuote 中文 20 字, 停 3 秒 | 5-6s | **欠 2-3 秒** |
| KeyNumber 主标 + 描述共 12 字, 停 2 秒 | 4s | **欠 2 秒** |
| TitleCard 章节标题 8 字, 停 3 秒 | 5s | **欠 2 秒** |

→ **vocut 所有带字组件的停留时长系统性偏短 2 秒左右**，这就是"都有点快"的字面解释。

---

## 对 vocut 的转化

**plan.py 新增**：`_compute_min_duration_by_text(scene_payload)`

```python
def _compute_min_duration_by_text(scene_payload: dict) -> float:
    """BBC 标准：每中文字符至少 0.3 秒舒适停留"""
    text_fields = ["primary", "secondary", "body", "quote", "title"]
    total_chars = 0
    for f in text_fields:
        v = scene_payload.get(f, "")
        if isinstance(v, str):
            # 中文字符按 1 计, 英文/数字按 0.4 计
            total_chars += sum(1 if ord(c) > 127 else 0.4 for c in v)
    return max(2.0, total_chars * 0.3)
```

然后在 LLM 输出 `duration_seconds` 之后强制 `max(llm_duration, _compute_min_duration_by_text(payload))`。

→ LLM 想给 2 秒, 但文字 20 字, 强制改 5 秒。
