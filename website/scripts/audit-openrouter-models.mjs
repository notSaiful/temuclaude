const models = ['moonshotai/kimi-k3', 'z-ai/glm-5.2', 'x-ai/grok-4.5'];
const response = await fetch('https://openrouter.ai/api/v1/models');
if (!response.ok) throw new Error(`OpenRouter model catalog request failed: ${response.status}`);
const catalog = await response.json();
const available = new Set((catalog.data || []).map((model) => model.id));
const missing = models.filter((model) => !available.has(model));
if (missing.length) throw new Error(`Approved model(s) unavailable: ${missing.join(', ')}`);
console.log(`Approved models available: ${models.join(', ')}`);
