"""Static safety contracts for the Vercel media-job bridge."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_media_jobs_are_persistent_owner_scoped_and_credit_settled():
    migration = (ROOT / "supabase/migrations/202607130004_media_jobs.sql").read_text()

    for required in (
        "temuclaude_media_jobs",
        "enable row level security",
        "temuclaude_reserve_media_credits",
        "temuclaude_settle_media_job",
        "credits_reserved",
        "grant execute",
    ):
        assert required in migration


def test_media_route_requires_authentication_and_never_exposes_provider_key():
    create_route = (ROOT / "website/app/api/media/jobs/route.ts").read_text()
    implementation = (ROOT / "website/lib/media-jobs.ts").read_text()

    assert "getAuthenticatedSupabaseUser" in create_route
    assert "MEDIA_ENABLED_PLANS" in create_route
    assert "AIML_API_KEY" in implementation
    assert "process.env.AIML_API_KEY" not in (ROOT / "website/app/playground/page.tsx").read_text()
    assert "new URL(value)" in implementation
    assert "parsed.protocol === 'https:'" in implementation


def test_playground_has_explicit_output_selection_and_native_players():
    page = (ROOT / "website/app/playground/page.tsx").read_text()
    media_intent = (ROOT / "website/lib/media-intent.ts").read_text()

    for required in ('inferMediaKind(input)', '<video controls', '<audio controls'):
        assert required in page
    assert 'aria-label="Choose output type"' not in page
    for required in ('return \'video\'', 'return \'music\'', 'return \'speech\'', 'return \'image\''):
        assert required in media_intent
