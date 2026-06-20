# Project Alignment

Use these repo-specific constraints when auditing or polishing the UI.

## Product Direction

- The product is a Saju analysis dashboard and report system.
- The UI should feel analytical, calm, modern, and trustworthy.
- The visual baseline is closer to Toss and financial analytics products than to mystical, editorial, or ornamental fortune-telling sites.

## Existing Technical Baseline

- Frontend stack: Next.js 14, React 18, Tailwind CSS, Framer Motion
- Fonts are loaded locally through `next/font/local` in `frontend/src/app/layout.tsx`
- The active design direction is token-driven and component-driven, not page-by-page art direction
- The core design-system spec already emphasizes light mode, mobile-first readability, rounded surfaces, and restrained motion

## What Good Design Review Looks Like Here

- stronger hierarchy without louder noise
- tighter spacing systems, not random pixel nudges
- stable report readability on mobile widths
- clear CTA and status emphasis
- minimal chrome around the actual analysis content

## What to Avoid

- treating this like a generic SaaS landing-page audit
- decorative spirituality motifs as a shortcut for "brand"
- over-polishing with gradients, blobs, or ornamental shadows
- turning every section into a card when layout would communicate better
- judging the UI without checking the rendered state
