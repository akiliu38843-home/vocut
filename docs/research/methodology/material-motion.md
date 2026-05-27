# Material Design Motion (M1 + M3)

## Material 3 — current spec

### Easing curves (cubic-bezier)
- **Standard**: `cubic-bezier(0.2, 0, 0, 1)` — most common UI motion
- **Standard decelerate**: `cubic-bezier(0, 0, 0, 1)` — entering elements
- **Standard accelerate**: `cubic-bezier(0.3, 0, 1, 1)` — exiting elements
- **Emphasized**: complex path (hero / prominent moments)
- **Emphasized decelerate**: `cubic-bezier(0.05, 0.7, 0.1, 1)`
- **Emphasized accelerate**: `cubic-bezier(0.3, 0, 0.8, 0.15)`
- **Linear**: `cubic-bezier(0, 0, 1, 1)` — only for indeterminate progress

### Duration tokens (ms)
- **Short**: 50 / 100 / 150 / 200
- **Medium**: 250 / 300 / 350 / 400
- **Long**: 450 / 500 / 550 / 600
- **Extra long**: 700 / 800 / 900 / 1000

### Usage
- Standard curves for utility / data-dense
- Emphasized for hero / brand moments
- Larger movement = longer duration (proportional)
- Pair entrance + exit curves (decelerate + accelerate)

---

## Material 1 — legacy with cubic-bezier values (still authoritative for basics)

### Easing curves
- **Standard**: `cubic-bezier(0.4, 0.0, 0.2, 1)` — "quickly accelerate, slowly decelerate"
- **Deceleration**: `cubic-bezier(0.0, 0.0, 0.2, 1)` — entering full velocity, slowing
- **Acceleration**: `cubic-bezier(0.4, 0.0, 1, 1)` — exiting at full velocity
- **Sharp**: `cubic-bezier(0.4, 0.0, 0.6, 1)` — symmetric accel + decel (return-trip elements)

### Duration baselines
- Mobile: **300ms baseline**, 225ms enter, 195ms exit, up to 375ms complex
- Tablet: ~30% longer (390ms)
- Wearables: ~30% shorter (210ms)
- Desktop: 150-200ms

### When to use
- **Standard**: growing/shrinking on screen
- **Deceleration**: entering screen with scale/opacity
- **Acceleration**: leaving screen with scale/opacity
- **Sharp**: elements that may reappear (symmetric)

Sources:
- https://m3.material.io/styles/motion/easing-and-duration/tokens-specs
- https://m1.material.io/motion/duration-easing.html
