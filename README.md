# PAIM

Parish Agricultural Information and Market Linkage. Django API + realtime backend
(`apps/`, `config/`), React frontend (`frontend/`) — see `IMPLEMENTATION_REACT.md`.

**New to the repo?** Follow **[INSTALL.md](INSTALL.md)** for a full setup on Windows, macOS, and Linux.

## Backend

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/python manage.py migrate
```

### Create an admin account

```bash
.venv/bin/python manage.py createsuperuser
```

You'll be prompted for phone, full name and password. A superuser is always created
with `role=national_admin` and `scope_level=national` — those two fields are set
automatically, so there's nothing else to fill in. Sign in with this account at
`/sign-in` in the frontend (not `/admin/` — that's Django's own admin, a separate
UI from the React app) to reach the national dashboard and the configuration panel
at `/national/admin` (users, geography, crops, seasons, farmers, buyers).

### Seed demo data

```bash
.venv/bin/python manage.py seed_demo            # populate
.venv/bin/python manage.py seed_demo --reset    # wipe and repopulate
```

Seeds a realistic Ugandan dataset — 3 districts (Mukono, Wakiso, Jinja) with
subcounties/parishes/villages, Maize and Coffee, 40 farmers, three seasons (two
closed and settled, one in progress), a full market cycle (declarations, sealed
bids, awards, settlements), rolled-up parish/district/national metrics, and a
couple of trend insights. It's scoped by district name, so `--reset` only touches
data it created — anything else in your database is untouched.

The command prints a table of accounts to sign in as when it finishes. Every
seeded account (agents, chiefs, officers, buyers, the farmer logins) shares the
password `demo1234`.

Requires Redis to fully succeed silently (see below) — without it you'll see
harmless `realtime publish failed` tracebacks in the output as each market event
tries and fails to publish; the data itself still seeds correctly either way.

### Run the server

```bash
.venv/bin/uvicorn config.asgi:application --reload --port 8000   # ASGI, so websockets work
```

Health check: `http://127.0.0.1:8000/healthz`. API docs: `http://127.0.0.1:8000/api/v1/docs/`.

Core domain rules live in `apps/*/services.py`; read paths live in `selectors.py`.
Realtime (Channels) lives in `apps/realtime/`; it reuses `parish_ids_for()` from
`apps/accounts/scoping.py` so HTTP and WebSocket enforce the same scope rule.

Websockets need Redis (`docker compose up redis`, or set `REDIS_URL`). Tests use an
in-memory channel layer (`config/settings/test.py`) and need no Redis.

```bash
.venv/bin/pytest
```

## Frontend

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173, proxies /api and /ws to :8000
npm run gen:api       # regenerate src/api/schema.d.ts from the running backend
```

`src/api/schema.d.ts` is generated — never hand-edit it. `npm run build` type-checks
and produces the production bundle; `npm run lint` enforces the feature import
boundary (`features/*` may import `design/`, `api/`, `realtime/`, never another
feature); `npm test` runs Vitest; `npm run bundlewatch` checks the built bundles
against `.bundlewatch.config.json` (run `npm run build` first).

Both servers need to be running at once — visit `http://localhost:5173`, not the
Django port. A national admin (see above) can reach the configuration panel at
`/national/admin`; every other role lands on its own home after signing in.
