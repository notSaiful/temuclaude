# Staging setup

Staging must use separate Supabase, Fly, and Vercel projects. Never reuse the
production service-role key, E2B key, or provider credentials.

1. Create a Supabase project and save its project reference, URL, anon key,
   and a server-only secret key. Apply the committed migrations with
   `supabase link --project-ref <staging-ref>` then `supabase db push`.
2. Create `temuclaude-staging` in Fly. Set `TEMUCLAUDE_API_KEY` and
   `OPENROUTER_API_KEY` with `fly secrets set -c fly.staging.toml ...`; do not
   add keys to `fly.staging.toml`. Deploy using `fly deploy -c fly.staging.toml`.
3. Create a separate Vercel project rooted at `website/`. Add values from
   `website/.env.staging.example` only to the Vercel Preview environment.
4. Configure Supabase Auth redirect URLs for the staging domain and test OTP,
   project ownership, file export, and an E2B preview using a disposable user.
5. Run the migration workflow only after its production environment approval is
   configured. Do not point staging at the production project reference.

The Python Fly API accepts only `Authorization: Bearer $TEMUCLAUDE_API_KEY`.
Its CORS list is opt-in via `TEMUCLAUDE_CORS_ORIGINS`; leave it unset if only
server-to-server access is required.
