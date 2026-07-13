-- Expand the approval workflow with explicitly reviewed, isolated execution
-- actions. The Next.js server remains responsible for ownership checks.
alter table public.temuclaude_project_actions
  drop constraint if exists temuclaude_project_actions_action_type_check;

alter table public.temuclaude_project_actions
  add constraint temuclaude_project_actions_action_type_check
  check (action_type in (
    'agent.run', 'file.write', 'command.run', 'package.install',
    'network.enable', 'browser.run', 'github.connect',
    'deploy.preview', 'deploy.production'
  ));
