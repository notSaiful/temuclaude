# TemuClaude

TemuClaude gives one answer from a pool of AI models. It starts with the least
expensive model likely to succeed and adds a specialist or a second check only
when the request needs it.

The primary objective is simple: reliable answers without paying for
unnecessary model calls.

## Live services

- Website: https://temuclaude.com
- Playground: https://temuclaude.com/playground
- API base URL: `https://temuclaude.com/v1`
- API model: `temuclaude`

Create an API key in the dashboard and send OpenAI-compatible chat completion
requests to `/v1/chat/completions`. Keep keys in a local secret store.

## How a request is handled

1. Validate authentication, input, and usage limits.
2. Identify the task and estimate its difficulty.
3. Choose the lowest-cost suitable model.
4. Add a specialist or independent check only when useful.
5. Return one answer and record completed usage.

The playground uses the same routing policy as the API. Long playground
requests run through Cloud Run so they are not limited by Vercel's five-minute
request ceiling.

Model availability changes over time. Runtime identifiers and fallbacks are
kept in code and tested against the provider catalog; this README intentionally
does not duplicate a model or pricing table.

## Local development

Requirements:

- Node.js 22+
- Python 3.11+

Website setup:

```bash
cd website
npm ci
cp .env.example .env
npm run build
```

Add required values to `website/.env`. Never commit credentials.

Python checks:

```bash
python -m pytest
python -m compileall -q src
```

Production checks:

```bash
cd website
npm run production:gates
```

## Repository map

- `website/`: Next.js website, playground, and API routes
- `src/`: Python routing and verification engine
- `tests/`: Python and cross-service contract tests
- `benchmarks/`: repeatable evaluation tools
- `research/`: evidence and implementation findings
- `docs/`: deployment and integration documentation
- `ROADMAP.md`: the only active product plan

## Safety and release policy

- Authentication must complete before any paid model call.
- Credentials stay in server-side environment variables or a secret manager.
- Model changes require tests and a rollback path.
- Public quality claims require reproducible evidence.
- Generated state, dependency folders, and local environment files are not
  source artifacts.

See [ROADMAP.md](ROADMAP.md) for current priorities.

## License

MIT. See [LICENSE](LICENSE).
