# Launch checklist

## Required before production traffic

- [ ] Rotate any credential that was ever committed, pasted into a ticket, or shared outside its intended secret store.
- [ ] Set `TEMUCLAUDE_API_KEY` as a Fly secret; it must differ from all website and provider keys.
- [ ] Set provider, Supabase, email, and E2B secrets only in their respective production secret stores.
- [ ] Confirm `ALLOW_EPHEMERAL_DB=false` and `NEXT_PUBLIC_BILLING_CHECKOUT_ENABLED=false`.
- [ ] Apply and verify all Supabase migrations in staging, then production using the protected manual workflow.
- [ ] Run `pytest tests/ -v --tb=short -x`, `python -m py_compile api_server.py`, `cd website && npm ci && npx tsc --noEmit && npm run build`.
- [ ] Deploy Fly and verify `/health`; verify the API rejects a missing or invalid bearer token.
- [ ] Verify Vercel production and preview builds independently.
- [ ] Configure error monitoring and on-call ownership before enabling traffic.

## Explicitly unavailable until separately implemented and tested

GitHub App installation, Vercel OAuth/customer-owned deployment, package
installation, arbitrary command execution, and production promotion must remain
hidden or disabled. Each requires explicit approval records, least-privilege
credentials, budget limits, revocation, and end-to-end tests before launch.
