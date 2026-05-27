# Apple Human Interface Guidelines — Motion

Source: https://developer.apple.com/design/human-interface-guidelines/motion
（页面 JS 渲染抓不到，本文是搜索 + Medium 二手总结，标注"间接"）

## 动效要传达什么
- 状态（state）
- 反馈（feedback）
- 层级和空间关系（hierarchy & spatial relationships）
- 增强视觉体验，但服务功能

## 时长
- **理想范围: 100ms - 500ms**
  - 100ms 以内观众感觉不到
  - 500ms 以上观众觉得卡
- 研究依据: UI / HCI 学界共识

## 缓动
- **ease-in-ease-out**: 起始慢、中间快、末尾慢 — Apple 的默认 pacing
- iOS 默认走 **spring**（弹簧物理曲线），不是死的 cubic-bezier
- WatchKit 强制 built-in ease，不可关

## 反对的做法
- **不要做无意义的动效**（"不能为动而动"）
- **多个动效同时跑**（互相竞争注意力）
- 长时长用在高频交互（hover/press 不超过 150ms）

## 无障碍
- 必须支持 "Reduce Motion" 系统设置
- 用户开了 Reduce Motion: 跳过非必要动画，或用 fade 代替 motion

## 设计概念
- **Layers**: 用层级和阴影传达空间关系
- **Transitions**: 用过渡保持上下文连续
- **Depth via shadow + blur**: 阴影建立深度
- **Continuity**: 自然动效保证连贯感
