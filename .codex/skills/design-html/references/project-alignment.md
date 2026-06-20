# Project Alignment

Use these repo-specific constraints when generating HTML reference artifacts.

## Product Direction

- The product is a Saju analysis dashboard and report system.
- The interface should feel analytical, modern, and trustworthy.
- The default visual baseline is the existing Toss-like design direction, not a mystical or ornamental fortune site.

## Existing Technical Baseline

- Frontend stack: Next.js 14, React 18, Tailwind CSS, Framer Motion
- Fonts are already loaded through `next/font/local` in the app shell
- The current design-system spec is token-driven and component-driven, not ad hoc page styling

This skill does not replace that frontend architecture. It produces a standalone artifact that helps finalize and communicate page-level design.

## What Good Output Looks Like Here

- clear content hierarchy
- calm surfaces
- strong mobile readability
- realistic Korean product copy when appropriate
- spacing and typography choices that could plausibly map back to the existing frontend system

## What to Avoid

- decorative spirituality motifs as the main identity
- generic centered startup hero templates
- arbitrary colors and spacing that fight the repo’s design-governance direction
- HTML that looks good only at one viewport
