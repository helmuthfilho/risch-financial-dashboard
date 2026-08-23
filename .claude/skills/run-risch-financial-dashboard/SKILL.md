---
name: run-risch-financial-dashboard
description: Build, run, and drive the risch-financial-dashboard Next.js app (personal finance dashboard). Use when asked to start the app, run its dev server, build it, run its tests/lint, take a screenshot of its UI, or interact with the running pages (Renda Variável, Renda Fixa, Gastos).
---

Next.js (App Router) + TypeScript web app backed by PostgreSQL (via Prisma).
`chromium-cli` was not available in this environment, so drive it via the
headless-Chromium Playwright REPL at
`.claude/skills/run-risch-financial-dashboard/driver.mjs` — same command
vocabulary as `chromium-cli` (`nav`, `wait-for`, `screenshot`, `click`, ...).

All paths below are relative to the repo root.

## Prerequisites

```bash
node -v   # tested with v20.18.1 — 20+ works; npm warns below 20.19 (harmless)
docker -v && docker compose version
```

Install Playwright's Chromium (one-time; downloads to `~/Library/Caches/ms-playwright` on macOS):

```bash
npx playwright install chromium --with-deps
```

## Setup

```bash
npm install
cp .env.example .env      # DATABASE_URL for the local Postgres below
docker compose up -d      # starts Postgres on localhost:5432
npx prisma migrate dev    # applies migrations (schema is currently empty)
```

## Build

```bash
npm run build   # production build; also the most reliable TypeScript check
                 # (bare `tsc --noEmit` fails: LayoutProps is only generated
                 # by `next dev`/`next build`)
```

## Run (agent path)

Start the dev server in the background and wait for it to actually serve:

```bash
nohup npm run dev > /tmp/nextdev.log 2>&1 & disown
for i in $(seq 1 30); do curl -sf http://localhost:3000 >/dev/null && break; sleep 1; done
```

(macOS's `curl`/shell here has no GNU `timeout`; the poll loop above is the
`timeout 30 bash -c 'until curl ...'` idiom adapted to work without it.)

Drive it by piping a script to the REPL's stdin — no tmux needed, the driver
serializes commands internally even when they all arrive in one buffered
heredoc:

```bash
node .claude/skills/run-risch-financial-dashboard/driver.mjs <<'EOF'
launch
nav http://localhost:3000
wait-for text=Dashboard Financeiro
screenshot 01-home
click text=Renda Fixa
wait-for text=Em construção
screenshot 02-renda-fixa
nav http://localhost:3000/api/health
text
console --errors
quit
EOF
```

Screenshots land in `/tmp/shots/` (override: `SCREENSHOT_DIR`).

For iterative/interactive use, wrap the same driver in `tmux` (`send-keys` /
`capture-pane`) if `tmux` is installed — it was not in this environment, so
the heredoc form above is what was actually verified.

Stop the dev server when done: `lsof -ti:3000 -sTCP:LISTEN | xargs -r kill`.

### Driver commands

| command                                            | what it does                                   |
| --------------------------------------------------- | ------------------------------------------------ |
| `launch`                                           | launch headless Chromium                       |
| `nav <url>`                                        | navigate                                       |
| `wait-for text=<text>` / `wait-for <css-selector>` | wait up to 10s                                 |
| `screenshot [name]`                                | full-page screenshot → `/tmp/shots/<name>.png` |
| `click text=<text>` / `click <css-selector>`       | click                                          |
| `fill <css-selector> <text...>`                    | fill an input                                  |
| `press <key>`                                      | keyboard key (e.g. `Enter`)                    |
| `text [css-selector]`                              | print `innerText` (body if no selector)        |
| `eval <js>`                                        | evaluate JS in the page, print JSON             |
| `url`                                              | print current URL                              |
| `console --errors`                                 | print captured `console.error`/page errors     |
| `quit`                                             | close the browser                              |

## Run (human path)

```bash
npm run dev   # → http://localhost:3000. Ctrl-C to stop.
```

## Test

```bash
npm run lint            # ESLint
npm run format:check    # Prettier
npm run test            # Vitest
npm run test:coverage   # Vitest + coverage; fails below 80% on src/lib/** (docs/adr/0004)
npm run build            # also validates TypeScript types
```

## Gotchas

- **No `chromium-cli` in this environment** → built `driver.mjs` with plain
  Playwright `chromium.launch()` instead of adapting `_electron` (this is a
  web app, not desktop) — same command vocabulary, drop-in replacement.
- **No `tmux` in this environment** → the heredoc form (`node driver.mjs
<<'EOF' ... EOF`) is the verified path. The driver's `readline` handler
  fires once per buffered line without waiting for the previous async
  command to finish, so a naive implementation races `nav` against `launch`
  and fails with `ERROR: launch first` on every command — the driver
  serializes lines through a promise queue (`driver.mjs`, near the bottom)
  specifically to make heredoc batches safe.
- **`.env*` in `.gitignore` also hides `.env.example`** by default — the
  project's `.gitignore` adds `!.env.example` so the template stays tracked
  while the real `.env` doesn't.
- **`npm audit` reports 3 "high" findings** in `deepmerge-ts` (transitive,
  via `@prisma/config`) — a stack-exhaustion DoS in the Prisma CLI's config
  loader, not exposed at runtime. Left as-is; `npm audit fix --force` would
  downgrade `prisma` to 6.12.0.

## Troubleshooting

- **`EADDRINUSE` on port 3000**: a previous dev server is still running →
  `lsof -ti:3000 -sTCP:LISTEN | xargs -r kill`, then restart.
- **`/api/health` returns `{"status":"error","database":"disconnected"}`**:
  Postgres isn't running or `.env` doesn't match `docker-compose.yml` → check
  `docker compose ps`, re-run `docker compose up -d`.
- **Driver hangs / every command prints `ERROR: launch first`**: you're
  running an older copy of `driver.mjs` without the promise-queue fix
  described in Gotchas — pull the current version.
- **`Executable doesn't exist at .../chromium...`**: Playwright browsers
  not installed → `npx playwright install chromium --with-deps`.
