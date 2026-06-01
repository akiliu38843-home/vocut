# Walter Murch · 六法则 (Rule of Six)

**来源**：Walter Murch《In the Blink of an Eye》(Silman-James Press, 2nd ed. 2001)
**作者身份**：剪辑师，《现代启示录》《英国病人》(奥斯卡最佳剪辑)、《教父》三部曲
**参考链接**：
- [StudioBinder · The Rule of Six](https://www.studiobinder.com/blog/walter-murch-rule-of-six/)
- [Berkeley iSchool · The Rule of Six](https://blogs.ischool.berkeley.edu/i290-viznarr-s12/the-rule-of-six-walter-murch/)
- [原书 PDF (Craft Film School)](https://www.craftfilmschool.com/userfiles/files/Walter%20Murch%20-%20In%20the%20Blink%20of%20an%20Eye%20Revised%202nd%20Edition%20(2001,%20Silman-James%20Pr).pdf)

---

## 一句话总结

**判断"这一刀该不该剪"的时候，按 6 个维度打分，但前 3 个的权重远大于后 3 个。**

---

## 六个维度 + 权重

| 序 | 英文 | 中文 | 权重 | 大白话 |
|---|---|---|---|---|
| 1 | Emotion | 情绪 | **51%** | 这一刀剪完，观众的感受对不对？(最重要) |
| 2 | Story | 故事 | **23%** | 这一刀有没有把剧情往前推？ |
| 3 | Rhythm | 节奏 | **10%** | 这一刀在不在节拍上？ |
| 4 | Eye-trace | 视觉引导 | 7% | 观众眼睛刚才看哪儿、下一帧引到哪儿？ |
| 5 | 2D Plane | 屏幕二维构图 | 5% | 切完构图有没有突然变丑 / 主体位置跳 |
| 6 | 3D Space | 三维空间连续性 | 4% | 切完空间方位还连得上吗 (180°轴线) |

---

## 关键洞见 (Murch 原话精神)

> **顶上 2 个 (情绪 + 故事 = 74%)** 比下面 4 个的总和 (26%) 重得多。
> 而 **情绪一个就抵下面 5 个的总和**。
>
> 如果你必须舍弃一项：
>
> - 永远不要为了"故事"舍弃"情绪"
> - 不要为了"节奏"舍弃"故事"
> - 不要为了"视觉引导"舍弃"节奏"
> - 不要为了"二维构图"舍弃"视觉引导"
> - 不要为了"三维连续性"舍弃"二维构图"

**剪辑 = 视觉音乐 (visual music)**。节奏是"剪辑的音乐"。

---

## 对 vocut 的拷问

vocut 目前只动了：
- 节奏 (10%) —— 通过 transition duration 控制
- 二维构图 (5%) —— 通过组件 layout / TYPE_RATIO 控制

**没动**：
- 情绪 (51%) —— LLM prompt 里**没有任何"这段情绪是啥"的判断**
- 故事 (23%) —— LLM prompt 里**没有"这一段在剧本的哪个起承转合"的判断**
- 视觉引导 (7%) —— 组件之间**没有任何**"上段视线落点 → 下段主体位置"的衔接逻辑

→ **vocut 当前只覆盖了 15% 权重，丢了 81% 权重 (情绪+故事+视觉引导)。**

这是 "都有点快" 反馈的根因之一：**节奏只占 10%，但 vocut 把它当成了唯一旋钮。**
