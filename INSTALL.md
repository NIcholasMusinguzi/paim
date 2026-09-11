# PAIM installation guide

This guide installs **PAIM** (Parish Agricultural Information and Market Linkage) for local development: a Django API on port **8000** and a React app on port **5173**.

You need **two terminals** once setup is done — one for the API, one for the frontend. Always open the app at **http://localhost:5173**, not the Django port.

| What | Version |
|---|---|
| Python | **3.10, 3.11, or 3.12** (3.12 recommended) |
| Node.js | **20 LTS** or **22 LTS** |
| npm | comes with Node.js |
| Git | any recent version |
| Redis | optional, recommended for live updates and a quiet `seed_demo` |
| PostgreSQL | optional — SQLite is the default |

---

## 1. Install prerequisites

### Windows

1. Install [Python 3.12](https://www.python.org/downloads/). On the installer, tick **Add python.exe to PATH**.
2. Install [Node.js 22 LTS](https://nodejs.org/) (includes npm).
3. Install [Git for Windows](https://git-scm.com/download/win).
4. Optional: [Docker Desktop](https://www.docker.com/products/docker-desktop/) if you want Redis with one command.

Check in **PowerShell** or **Command Prompt**:

```bat
python --version
node --version
npm --version
git --version
```

If `python` is not found, try `py -3 --version`.

**WSL2 (optional).** Ubuntu on WSL works well; follow the Linux section inside the WSL terminal.

### macOS

Install [Homebrew](https://brew.sh/) if you do not have it, then:

```bash
brew install python@3.12 node git
```

Or install [Python](https://www.python.org/downloads/) and [Node.js LTS](https://nodejs.org/) from their websites.

Xcode command-line tools are required for some Python packages (including ReportLab):

```bash
xcode-select --install
```

Check:

```bash
python3 --version
node --version
npm --version
git --version
```

### Linux (Ubuntu / Debian)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git curl
```

Node 20 via NodeSource (Ubuntu’s default Node is often too old):

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

Fedora / RHEL:

```bash
sudo dnf install -y python3 python3-pip git nodejs npm
```

Check:

```bash
python3 --version
node --version
npm --version
git --version
```

---

## 2. Get the code

```bash
git clone https://github.com/NIcholasMusinguzi/paim.git
cd paim
```

If you already have the folder, `cd` into it instead.

---

## 3. Backend (Django API)

### Create a virtual environment

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks the script, run this once as Administrator, then retry:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

**Windows (Command Prompt)**

```bat
py -3 -m venv .venv
.venv\Scripts\activate.bat
```

Your prompt should show `(.venv)`.

### Install Python packages

From the **project root** (`paim/`), with the venv active:

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

### Environment file (optional for local SQLite)

Copy the example file. Dev settings already use SQLite and allow `http://localhost:5173`. A `.env` file is not required to start locally.

```bash
cp .env.example .env
```

Windows Command Prompt: `copy .env.example .env`

### Database

```bash
python manage.py migrate
```

This creates `db.sqlite3` in the project root. You do not need PostgreSQL for a first run.

### Redis (recommended)

Live updates (lots closing, bids, metrics) go through Redis. Without it the app still runs; you may see `realtime publish failed` / Redis connection errors. Data still saves.

**With Docker** (any OS, from the project root):

```bash
docker compose up redis -d
```

**Without Docker**

- macOS: `brew install redis && brew services start redis`
- Ubuntu: `sudo apt install -y redis-server && sudo systemctl start redis-server`
- Windows: use Docker, or [Memurai](https://www.memurai.com/) / WSL Redis

Confirm: `redis-cli ping` should print `PONG`.

### Seed demo data (optional but useful)

```bash
python manage.py seed_demo
```

If demo data already exists:

```bash
python manage.py seed_demo --reset
```

The command prints phone numbers to sign in with. **Every seeded account uses password `demo1234`.**

### Create your own national admin (optional)

Skip this if you seeded demo data (a national admin is already created).

```bash
python manage.py createsuperuser
```

You will be asked for **phone**, **full name**, and **password**. Role is set to national admin automatically.

### Start the API

Keep this terminal open:

```bash
python -m uvicorn config.asgi:application --reload --port 8000
```

Checks:

- Health: http://127.0.0.1:8000/healthz
- API docs: http://127.0.0.1:8000/api/v1/docs/

Do **not** use `python manage.py runserver` if you need WebSockets; uvicorn serves the ASGI app.

---

## 4. Frontend (React)

Open a **second terminal**. On Windows, activate the venv only for the backend — the frontend uses npm.

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**

Vite proxies `/api` and `/ws` to port 8000, so the API must already be running.

---

## 5. Sign in

| Role | Where you land |
|---|---|
| National admin | `/national` — dashboards and `/national/admin` |
| District / parish officers | scoped dashboards |
| Farmer | `/farmer` |
| Agent | `/agent` |
| Buyer | `/buyer` |

Use a seeded phone + `demo1234`, or the superuser you created.

Django’s own admin at http://127.0.0.1:8000/admin/ is separate from the React app.

---

## 6. Daily workflow

**Terminal 1 — API** (venv active, project root):

```bash
python -m uvicorn config.asgi:application --reload --port 8000
```

**Terminal 2 — UI** (`frontend/`):

```bash
npm run dev
```

Optional Redis:

```bash
docker compose up redis -d
```

---

## 7. Tests

**Backend** (venv active, project root):

```bash
pytest
```

Tests use an in-memory channel layer — Redis is not required.

**Frontend** (`frontend/`):

```bash
npm test
npm run lint
```

---

## 8. Optional: PostgreSQL instead of SQLite

```bash
docker compose up db -d
```

Point `DATABASE_URL` at Postgres if your settings read it. The default `config.settings.dev` still uses SQLite unless you change `DATABASES` in settings. For a first install, stay on SQLite.

---

## 9. Troubleshooting

| Problem | What to try |
|---|---|
| `python` / `python3` not found | Reinstall Python and tick PATH (Windows), or use `py -3` |
| `venv` fails on Ubuntu | `sudo apt install python3-venv` |
| PowerShell `Activate.ps1` is blocked | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `pip install` fails on macOS (ReportLab) | `xcode-select --install` |
| API starts but UI shows network errors | Confirm uvicorn is on **8000** and you opened **5173** |
| `realtime publish failed` / Redis `ConnectionError` | Start Redis or ignore it for a first demo |
| `seed_demo` says data already present | `python manage.py seed_demo --reset` |
| Port 8000 or 5173 in use | Stop the other process, or change `--port` / Vite port |
| Node too old | Install Node 20+; `node --version` |
| Windows long-path npm errors | Enable long paths, or clone closer to `C:\` |

---

## 10. Quick command cheat sheet

After the venv exists, **macOS/Linux** uses `.venv/bin/python`. **Windows** uses `.venv\Scripts\python.exe`. With the venv **activated**, `python` works on all three.

```bash
# backend
python -m pip install -e ".[dev]"
python manage.py migrate
python manage.py seed_demo --reset
python -m uvicorn config.asgi:application --reload --port 8000
pytest

# frontend
cd frontend
npm install
npm run dev
```
