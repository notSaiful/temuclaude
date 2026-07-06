# Mobile App: {{ PROJECT_NAME }}

## Core Concept
{{ RAW_PROMPT }}

## User Flows
1. Onboarding → Permission requests → Home screen
2. Home → Select action → Perform → Result/confirmation
3. Profile → Edit → Save → Updated
4. Settings → Toggle preference → Persisted

## Data Models
- **User**: id, name, email, avatar, preferences
- **Content**: id, title, body, image, timestamp, author
- **Notification**: id, type, title, body, read, timestamp

## UI Specification

### Color System
- Primary: {{ COLORS }}
- Neutrals: gray-50, gray-100, gray-900
- Accent: secondary color for highlights

### Typography
- Heading: {{ FONTS }}
- Body: {{ FONTS }}
- Scale: iOS dynamic type / Android font scale support

### Component Library
- NativeWind (Tailwind for React Native)
- Expo Router for navigation
- Custom components: Button, Card, Input, List, Avatar, Badge
- Bottom tab bar + stack navigation

### Screens
- **/onboarding** — 3-slide intro carousel → permission requests
- **/(tabs)/home** — Feed/list view with pull-to-refresh
- **/(tabs)/search** — Search input + results list
- **/(tabs)/notifications** — Notification list with read/unread
- **/(tabs)/profile** — User profile + edit + settings link
- **/detail/[id]** — Detail view with header, content, actions
- **/settings** — Preferences toggles, theme, about

## Technical Constraints
- Stack: Expo (SDK 52+), React Native, NativeWind, Expo Router
- TypeScript strict
- Offline support: AsyncStorage + sync on reconnect
- Push notifications: Expo Notifications
- Analytics: PostHog or Mixpanel
- Deep linking support

## Gestures & Interactions
- Swipe right: Go back
- Swipe down: Pull to refresh
- Long press: Context menu / selection
- Pinch: Zoom on images
- Tap: Navigate / select
- Double tap: Like/save action

## Responsive
- iOS: Safe area insets, notch handling
- Android: Status bar, navigation bar
- Tablet: Split view on larger screens

## States Required
- Loading: Shimmer placeholders
- Error: Retry with icon + message
- Empty: Illustration + helpful text + CTA
- Offline: Banner + cached content

## Quality Bar
{{ QUALITY_BAR }}

## Keywords Matched
{{ KEYWORDS_MATCHED }}