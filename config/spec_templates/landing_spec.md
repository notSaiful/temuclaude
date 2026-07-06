# Landing Page: {{ PROJECT_NAME }}

## Core Concept
{{ RAW_PROMPT }}

## Target Audience
{{ TARGET_AUDIENCE }}

## Brand
{{ BRAND }}

## Sections (in order)
1. **Hero**: Headline + subheadline + CTA + hero visual
2. **Social Proof**: Logo bar (5-7 trusted by logos)
3. **Features**: 3-column grid with icons, titles, descriptions
4. **How It Works**: 3-step numbered process
5. **Testimonial**: Customer quote with avatar + name + role
6. **Pricing**: 3-tier pricing cards (Free, Pro, Enterprise)
7. **FAQ**: Accordion with 5-6 common questions
8. **CTA Footer**: Final call-to-action + signup form
9. **Footer**: Links, social, legal

## UI Specification

### Color System
- Primary: {{ COLORS }}
- Neutrals: white, gray-50, gray-100, gray-900
- Accent: gradient from primary to accent

### Typography
- Display/Heading: {{ FONTS }} — large, bold
- Body: {{ FONTS }}
- Scale: text-sm base, text-4xl/5xl/6xl for headlines

### Visual Style
- Modern, clean, lots of whitespace
- Subtle gradients and glows
- Framer Motion for scroll animations
- Glassmorphism on cards
- Smooth hover transitions

### Components
- Button (primary, secondary, ghost) with hover states
- Card with subtle shadow and border
- Accordion for FAQ
- Pricing cards with feature lists + checkmarks
- Logo cloud (grayscale, color on hover)
- Responsive grid system

## Technical Constraints
- Stack: Next.js 16, React 19, Tailwind v4, Framer Motion
- Mobile-first responsive
- SEO: meta tags, OpenGraph, structured data
- Performance: LCP < 2s, CLS < 0.1
- No layout shift on load

## Responsive
- Mobile: Single column, stacked sections, hamburger nav
- Tablet: 2-column features, compressed hero
- Desktop: Full multi-column, wide hero

## Animations
- Fade-in on scroll (Framer Motion whileInView)
- Stagger children in feature grid
- Hover scale on cards and buttons
- Smooth accordion expand/collapse
- Hero text slide-up on mount

## Quality Bar
{{ QUALITY_BAR }}

## Keywords Matched
{{ KEYWORDS_MATCHED }}