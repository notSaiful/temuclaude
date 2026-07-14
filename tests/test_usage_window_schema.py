"""Regression guards for usage windows that need precise event timestamps."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_usage_window_migration_has_durable_event_ledger_and_credit_columns():
    migration = (ROOT / "supabase/migrations/202607130001_usage_windows_and_analytics.sql").read_text()
    assert "add column if not exists credit_balance" in migration
    assert "add column if not exists credits_reset_at" in migration
    assert "create table if not exists public.temuclaude_usage_events" in migration
    assert "temuclaude_usage_events_user_created_idx" in migration


def test_rolling_window_does_not_claim_daily_rollups_are_five_hour_data():
    db = (ROOT / "website/lib/db.ts").read_text()
    assert "Usage event ledger is unavailable:" in db
    assert "falling back to daily" not in db
    assert "nextWeeklyResetAt(user.credits_reset_at, now)" in db
