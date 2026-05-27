# IBM Carbon Design System — Motion

Source: https://github.com/carbon-design-system/carbon/tree/main/packages/motion
（直接读源码，不是文档站）

## Duration tokens (ms)
| Token | Value | Use |
|---|---|---|
| `fast01` | **70ms** | Hover / press feedback |
| `fast02` | **110ms** | Quick UI response |
| `moderate01` | **150ms** | Standard transitions |
| `moderate02` | **240ms** | Expanding panels |
| `slow01` | **400ms** | Modals, dialogs |
| `slow02` | **700ms** | Large layout shifts |

## Easing curves (cubic-bezier 真值)

Carbon 有两套模式: **productive**（数据密集、效率优先）和 **expressive**（品牌时刻、情感）。

### Standard (general)
- Productive: `cubic-bezier(0.2, 0, 0.38, 0.9)`
- Expressive: `cubic-bezier(0.4, 0.14, 0.3, 1)`

### Entrance (元素入场)
- Productive: `cubic-bezier(0, 0, 0.38, 0.9)`
- Expressive: `cubic-bezier(0, 0, 0.3, 1)`

### Exit (元素出场)
- Productive: `cubic-bezier(0.2, 0, 1, 0.9)`
- Expressive: `cubic-bezier(0.4, 0.14, 1, 1)`

## 设计原则
- **Productive motion**: "creates a sense of efficiency and responsiveness, while remaining subtle and out of the way" — 用于用户专注完成任务时
- **Expressive motion**: "delivers enthusiastic, vibrant, and highly visible movement" — 用于品牌/情感时刻
- **Duration is dynamic**: 距离越大，时长越长（非线性缩放，提高感知一致性）
- **入场和出场配对使用** — 用同一系列的 entrance + exit
