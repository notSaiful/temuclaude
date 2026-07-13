export const MEDIA_KINDS = ['image', 'video', 'speech', 'music'] as const;
export type MediaKind = typeof MEDIA_KINDS[number];

/**
 * Conservative intent detector shared by the API and the playground.
 * It deliberately requires an output-oriented phrase so ordinary discussion
 * about music, images, or video remains a text answer instead of a charge.
 */
export function inferMediaKind(prompt: string): MediaKind | null {
  const text = prompt.trim().toLowerCase();
  if (!text) return null;
  if (/\b(generate|create|make|produce|render|animate)\b.{0,80}\b(video|animation|animated clip|film|footage|movie|motion graphics)\b|\bturn\b.{0,80}\binto (a )?video\b/.test(text)) return 'video';
  if (/\b(generate|create|make|compose|produce)\b.{0,80}\b(music|song|track|soundtrack|instrumental|beat|jingle)\b/.test(text)) return 'music';
  if (/\b(text[- ]to[- ]speech|voice[- ]?over|narration|read (this|it) aloud|speak (this|it))\b/.test(text)) return 'speech';
  if (/\b(generate|create|make|draw|design|render)\b.{0,80}\b(image|illustration|artwork|logo|poster|portrait|wallpaper|photo)\b|\b(draw|illustrate)\b/.test(text)) return 'image';
  return null;
}
