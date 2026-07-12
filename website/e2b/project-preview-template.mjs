import { Template, waitForTimeout } from 'e2b';

// This template intentionally contains only Node's standard runtime. User
// projects receive no TemuClaude, OpenRouter, GitHub, Vercel, or Supabase
// credentials; package installation and network egress remain disabled at run time.
export const PROJECT_PREVIEW_TEMPLATE = 'temuclaude-project-preview:v1';

export function createProjectPreviewTemplate() {
  return Template()
    .fromNodeImage('24')
    .makeDir('/home/user/project', { user: 'root' })
    .setWorkdir('/home/user/project')
    .setUser('user')
    .runCmd('node --version')
    .setStartCmd('sleep infinity', waitForTimeout(1_000));
}
