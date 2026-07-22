"""Regression contracts for durable maximum-quality generation jobs."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_generation_job_schema_has_durable_state_and_atomic_claim():
    migration = (ROOT / "supabase/migrations/202607220001_durable_generation_jobs.sql").read_text()

    for value in (
        "temuclaude_generation_jobs",
        "temuclaude_generation_job_events",
        "lease_token",
        "lease_expires_at",
        "cancel_requested",
        "temuclaude_claim_generation_job",
        "update public.temuclaude_generation_jobs",
    ):
        assert value in migration


def test_modal_submits_a_background_job_and_uses_the_long_execution_window():
    source = (ROOT / "modal_app.py").read_text()

    assert '@api.post("/v1/jobs/{job_id}/start")' in source
    assert "await run_generation_job.spawn.aio(job_id)" in source
    assert "timeout=86400" in source
    assert "temuclaude_claim_generation_job" in source
    assert "async def _durable_panel" in source
    assert "async def _durable_qa" in source
    assert "MAXIMUM_QUALITY_REPAIR_REVISIONS" in source
    assert "recover_generation_jobs" in source
    assert '"status": "waiting_retry"' in source


def test_playground_and_vercel_use_job_submission_not_a_long_artifact_request():
    playground = (ROOT / "website/app/playground/page.tsx").read_text()
    submit_route = (ROOT / "website/app/api/generation-jobs/route.ts").read_text()
    status_route = (ROOT / "website/app/api/generation-jobs/[jobId]/route.ts").read_text()

    assert "/api/generation-jobs" in playground
    assert "pollGenerationJob" in playground
    assert "This task will continue even if you close the Playground" in playground
    assert "status: 202" in submit_route
    assert "TEMUCLAUDE_MODAL_URL" in submit_route
    assert "export async function DELETE" in status_route


def test_maximum_quality_worker_persists_each_required_gate_and_recovers():
    source = (ROOT / "modal_app.py").read_text()
    migration = (ROOT / "supabase/migrations/202607220002_maximum_quality_pipeline.sql").read_text()

    for stage in (
        '"panel"',
        '"synthesis"',
        '"artifact"',
        '"sandbox_validation"',
        '"qa"',
        '"repair"',
    ):
        assert stage in source
    assert "_checkpoint_generation_stage" in source
    assert "_validate_html_artifact" in source
    assert "_run_isolated_preview" in source
    assert "MAXIMUM_QUALITY_MAX_WORKER_ATTEMPTS = 1000" in source
    assert "schedule=modal.Period(minutes=5)" in source
    assert '"p_lease_seconds": 900' in source
    assert "needs_review" in migration
    assert "temuclaude_recover_generation_jobs" in migration


def test_isolated_preview_has_an_internal_modal_worker_gateway():
    route = (ROOT / "website/app/api/internal/sandbox-validation/route.ts").read_text()

    assert "x-temuclaude-internal-key" in route
    assert "timingSafeEqual" in route
    assert "createIsolatedHtmlPreview" in route
