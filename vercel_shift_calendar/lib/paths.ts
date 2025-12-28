export function paths() {
  return {
    schedule: process.env.GITHUB_FILE_PATH || "shift_schedule.json",
    team: process.env.GITHUB_TEAM_SETTINGS_PATH || "team_settings.json",
    grad: process.env.GITHUB_GRAD_DAYS_PATH || "grad_days.json",
    exam: process.env.GITHUB_EXAM_PERIODS_PATH || "exam_periods.json",
  };
}
