# Council Web

Next.js 14 (App Router) frontend — the Council command center.

```
src/
  app/            routes: / (home), /inbox, /thoughts[/id], /agents[/id],
                  /tasks, /projects[/id], /reports, /memory, /activity, /settings
  components/
    shell/        sidebar, topbar, app-shell, command-palette
    talk/         talk-panel, recorder, thought-review
    agent/        agent-chat
    ui/           badges, states, page, agent-icon
  lib/            api client, hooks (TanStack Query), store (Zustand), utils
  types/          shared domain types (mirror backend)
```

See [`../../docs/development.md`](../../docs/development.md).
