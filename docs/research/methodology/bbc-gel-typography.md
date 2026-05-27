# BBC GEL Typography

Source: https://bbc.github.io/gel/foundations/typography/

## Font
- **Reith typeface** is the BBC's typographic identity, designed to "improve the experience of reading for everyone, regardless of ability, context or canvas"
- BBC has both Reith Sans and Reith Serif

## Type scale
- **Body text**: 15-18px depending on screen dimensions
- All sizes set in **relative units (em / rem)**, not pixels
- Sizes smaller than body should be used **sparingly** for supplementary info only

## Line-height (leading)
- **Body text minimum: 1.5 line-height** (WCAG standard)
- **1.375 recommended** for Reith Serif body
- **Large headings (h1/h2): 1.125** — reduced for vertical compactness
- Always use unitless multipliers (so it scales with font-size)

## Hierarchy
- Related elements need **greater white space** between them than unrelated ones
- Headings: **margin above ≈ 2x margin below** (2.75rem above / 1.375rem below)
- This maintains "vertical rhythm and cognitive grouping"

## Touch first
- BBC takes a "touch first" approach; type scale adjusts when non-touch input detected
