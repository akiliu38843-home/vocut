# Sergei Eisenstein · 蒙太奇五法

**来源**：Sergei Eisenstein《Film Form》《The Film Sense》(1929-1949)
**作者身份**：苏联导演，《战舰波将金号》(1925)、《十月》(1928)
**参考链接**：
- [StudioBinder · Soviet Montage Theory](https://www.studiobinder.com/blog/soviet-montage-theory/)
- [Media Studies · Eisenstein Montage](https://media-studies.com/eisenstein-montage/)
- [Fiveable · Eisenstein's theories of montage](https://fiveable.me/film-history-and-form/unit-10/eisensteins-theories-montage/study-guide/cl6nbp8Pq3pBpy9r)

---

## 一句话总结

**两个镜头拼一起，产生的意义大于两个镜头单独的意义之和。**
(蒙太奇 = 1 + 1 = 3)

---

## 五种蒙太奇 (从浅到深，后者包含前者)

### 1. 韵律 / 节拍蒙太奇 (Metric)
**怎么切**：按"帧数"切，到点就切，不管画面里在演什么。
**用场**：固定每 N 帧一切，制造机械、紧迫、催促感。
**大白话**：像节拍器，咔咔咔。
**对 vocut**：vocut 当前的 `transition_to_next` 时长固定 (fade 18 帧) 就是这个层次。

### 2. 节奏蒙太奇 (Rhythmic)
**怎么切**：看画面里的内容动得多快，跟着内容的节奏切。
**用场**：动作越激烈 → 切越快；安静越久 → 切越慢。
**大白话**：跟着画面里的事情走，不是跟着时钟走。
**对 vocut**：vocut **没有这层**。所有场景都按 LLM 输出的 duration_seconds 走，**没看画面/没看朗读音频的能量曲线**。

### 3. 调性蒙太奇 (Tonal)
**怎么切**：按镜头的**情绪色调**(明暗、冷暖、轻重)排序。
**用场**：把"悲伤的镜头"放一起，把"愤怒的镜头"放一起，让情绪累加。
**大白话**：按情绪相册排队。
**对 vocut**：vocut **完全没有**。LLM 选完场景就完了，不会按"这段在悲、这段在喜"重新编排。

### 4. 泛音蒙太奇 (Overtonal)
**怎么切**：上面 3 种 (节拍 + 节奏 + 调性) 一起用。
**大白话**：复调音乐。
**对 vocut**：高阶目标，先把前 3 层补上。

### 5. 智性蒙太奇 (Intellectual)
**怎么切**：用两个**没有时空关系**的镜头拼出**抽象观念**。
**经典例子**：《罢工》里"工人被屠杀" 切到 "屠宰场杀牛" → 观众脑里自动生成 "资本家把工人当牲口" 这个观念。
**对 vocut**：vocut 的 "key_number → pull_quote" 衔接本可以做到 (数据 + 引言 → 观点)，但当前 LLM prompt 没把这层写进去。

---

## 对 vocut 的拷问

vocut 当前停留在 **第 1 层 (节拍)**：每段 fade 18 帧，机械均匀。

**第 2 层 (节奏)** 才是治"都有点快"的关键：

> 18 个场景 / 60 秒 = 平均 3.3 秒/场景。
> 但 vocut **没有分辨**：
> - "数据冲击型"场景 (key_number) 该停短一点 (1.5-2s)
> - "观点陈述型"场景 (pull_quote) 该停长一点 (4-5s)
> - "氛围铺垫型"场景 (title_card) 该停最长 (5-7s)

所有场景被当成同质单元 → "都有点快"。

**第 3 层 (调性)** 是治"看完没记住啥"的关键：
当前 LLM 按剧本时间顺序排，**没有重排让情绪累加**。
