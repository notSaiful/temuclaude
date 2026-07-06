# App Spec: {{ PROJECT_NAME }}

## Core Concept
{{ RAW_PROMPT }}

## User Flows
1. Login → Dashboard → View key metrics
2. Select entity → View detail → Edit → Save
3. Filter/search → Apply filters → View results → Export
4. Settings → Configure preferences → Save

## Data Models
- **User**: id, name, email, role, avatar, created_at
- **Entity** (main domain object): id, name, status, owner_id, created_at, updated_at
- **Activity**: id, user_id, entity_id, action, timestamp
- **Settings**: id, user_id, theme, notifications, preferences

## UI Specification

### Color System
- Primary: {{ COLORS }}
- Neutrals: gray-50 through gray-900
- Accents: blue (info), green (success), amber (warning), red (error)
- Dark mode support required

### Typography
- Heading: {{ FONTS }}
- Body: {{ FONTS }}

### Component Library
- shadcn/ui (new-york style)
- Required: Card, Table, Button, Input, Select, Dialog, Tabs, Badge, Avatar, Dropdown
- Charts: Recharts (area, bar, line, pie)
- Forms: react-hook-form + zod validation

### Pages & Layouts
- **/** — Dashboard: KPI cards (4), activity feed, recent table, chart
- **/entities** — List view: table with search, filter, pagination
- **/entities/[id]** — Detail: tabs for overview, activity, settings
- **/settings** — User preferences form
- **Layout**: Sidebar nav + top bar (search, notifications, profile)

## Technical Constraints
- Stack: Next.js 16 App Router, React 19, Tailwind v4, TypeScript
- No localStorage for persistence (use cookies/server state)
- All auth via Supabase
- API routes for mutations, Server Components for reads
- SWR for data fetching (no useEffect fetch)

## Responsive Breakpoints
- Mobile (< 768px): Single column, hamburger menu
- Tablet (768-1024px): 2-column layout, collapsible sidebar
- Desktop (> 1024px): Full sidebar + multi-column

## States Required
- Loading: Skeleton screens for all data
- Error: Error boundary + retry button
- Empty: Empty state with illustration + CTA
- Offline: Connection status indicator

## Quality Bar
{{ QUALITY_BAR }}

## Keywords Matched
{{ KEYWORDS_MATCHED }}