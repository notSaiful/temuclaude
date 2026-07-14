export const FIVE_HOUR_WINDOW_SECONDS = 5 * 60 * 60;
export const WEEKLY_WINDOW_SECONDS = 7 * 24 * 60 * 60;

/**
 * Keep recurring weekly resets on their original cadence. Resetting from
 * `now` makes a late visit silently move the next renewal later every week.
 */
export function nextWeeklyResetAt(previousResetAt: number, now: number): number {
  if (!Number.isFinite(previousResetAt) || previousResetAt <= 0) {
    return now + WEEKLY_WINDOW_SECONDS;
  }
  if (previousResetAt > now) return previousResetAt;
  const elapsedPeriods = Math.floor((now - previousResetAt) / WEEKLY_WINDOW_SECONDS) + 1;
  return previousResetAt + elapsedPeriods * WEEKLY_WINDOW_SECONDS;
}

export function rollingWindowCutoff(now: number, hours = 5): number {
  return now - Math.max(1, hours) * 60 * 60;
}

export function nextRollingRecoveryAt(oldestRequestAt: number | null, hours = 5): number | null {
  return oldestRequestAt === null ? null : oldestRequestAt + Math.max(1, hours) * 60 * 60;
}
