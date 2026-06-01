# Edward Dmytryk · 剪辑七律

**来源**：Edward Dmytryk《On Film Editing》(Focal Press, 1984)
**作者身份**：好莱坞经典期剪辑师 → 导演，《凯恩号哗变》(1954)
**参考链接**：
- [NYFA · 7 Rules of Cutting](https://www.nyfa.edu/student-resources/what-you-can-learn-from-edward-dmytryks-7-rules-of-cutting/)
- [Pond5 · Dmytryk's 7 Rules vs Modern Post](https://blog.pond5.com/11775-how-dmytryks-7-rules-of-cutting-hold-up-to-modern-post-production/)
- [So The Theory Goes · 7 Rules of Cutting](https://www.sothetheorygoes.com/7-rules-of-cutting/)

---

## 一句话总结

**剪刀下手前先问 7 个问题，任何一条 yes 都不剪。**

---

## 七条规则

### 1. 没有正向理由，不要剪 (Never make a cut without a positive reason)

**大白话**：每一刀都要有一个能说出口的理由。"我觉得该切了"不算理由。
**对 vocut**：当前 LLM 是按"剧本句号切场景"，**没有判断"这一刀有没有理由"**。这是为啥很多 vocut 切口让人觉得"为切而切"。

### 2. 拿不准切早切晚的时候，宁可切晚一点 (Cut long rather than short)

**大白话**：留多一点比少一点强。观众宁可"等了半秒"，不要"还没看清就切走了"。
**对 vocut**：当前 vocut 的"3.3 秒平均"就是"切太短"的典型。Dmytryk 的建议是宁可 4 秒。

### 3. 能在动作里切就在动作里切 (Cut in movement)

**大白话**：镜头里有动作时切下去，观众的眼睛被动作牵着走，注意不到剪辑。在静止画面里切，剪辑会很显眼。
**对 vocut**：当前 vocut 全部 motion_graphic 场景都是**静态版式 + 弹簧入场**，组件入场动画结束后到下一段开始之间是**静止帧**，切口"咣"地一声。

### 4. 新鲜的优于陈旧的 (The fresh is preferable to the stale)

**大白话**：如果两个镜头都行，选信息更新、视角更新的那个。观众已经看过的视角，不要回头再看。
**对 vocut**：当前 LLM 没有"上一段已经展示过这个数据/这个 quote"的去重判断。

### 5. 场景应该带着动作进、带着动作出 (Begin and end with continuing action)

**大白话**：上一段结尾别让画面"停死"，下一段开头别让画面"从零开始"。
**对 vocut**：当前 vocut 每个场景是独立组件，**入场动画→静止停留→淡出**，每段都是从零开始/到零结束。这是 Dmytryk 明确反对的"乒乓球式"剪辑。

### 6. 为意义剪，不要为匹配剪 (Cut for proper values rather than proper matches)

**大白话**：意义对比技术连贯重要。哪怕画面接得不严丝合缝，只要意义对，就这么剪。
**对 vocut**：vocut 没有"匹配"问题 (因为各段独立)，但有相反问题：**只追求"风格匹配统一"，不追求"意义连贯"**。

### 7. 内容第一，形式第二 (Substance first—then form)

**大白话**：先把"这一段要说什么"想清楚，再去想"用什么形式呈现"。
**对 vocut**：vocut 的整个 plan.py LLM_SYSTEM_PROMPT 90% 在讲形式 (用什么组件、什么色板、什么动效)，只有 10% 在让 LLM 判断"这段要说什么"。**正好反过来。**

---

## 对 vocut 的拷问

7 条规则里 vocut 当前**违反了 5 条** (1、2、3、5、7)。

最致命的是 **#7 内容第一**：vocut 现在像一个"先选好衣服再找活儿干的人"。
LLM prompt 应该重写为：**先让 LLM 判断每段的"话语功能"** (开篇钩子 / 数据论证 / 观点抛出 / 案例佐证 / 情绪共鸣 / 收束) **再选组件**。
