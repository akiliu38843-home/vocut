# Atlassian Design Motion Principles

Source: https://atlassian.design/foundations/motion

## When motion is appropriate
- Clarify interactions and guide attention
- Provide feedback from user actions
- Support spatial changes (elements entering/exiting/moving)
- Reinforce brand moments during onboarding or milestones
- **"Motion is a clarifying layer, not decoration"**

## When motion is wrong
- Blocking workflow without adding meaning
- Running simultaneous animations that compete for attention
- High-frequency interactions (hover, press) with lengthy durations
- Missing start feedback or delayed response
- Motion that makes interface feel slower without context

## Duration & easing specifications
- **Interactions** (hover/press): 50–150ms
- **Transitions** (modals, panels entering): 150–400ms
- **Ease-out bold** `cubic-bezier(0, 0.4, 0, 1)` — elements arriving quickly
- **Ease-in-out bold** `cubic-bezier(0.4, 0, 0, 1)` — scaling/repositioning
- **Ease-in practical** `cubic-bezier(0.6, 0, 0.8, 0.6)` — exit transitions
- **Ease-out practical** `cubic-bezier(0.4, 1, 0.6, 1)` — subtle entrances

## Motion hierarchy
- **Small elements**: fast, understated (≤150ms)
- **Large elements**: longer, more expressive durations
- Exit faster than entrance to avoid workflow friction
- **Single focal point leads**; others support

## Named motion patterns
- Scale (growing/shrinking)
- Fade (opacity changes)
- Slide (X/Y axis movement)
- Color (background/border transitions)
