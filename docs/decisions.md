# Grid Stress Monitor - Decision Log

An append-only log of significant technical decisions.
Format: date, decision, alternatives considered, reason.

---

## 2026-05-25 - Moved credentials to .env file

**Decision:** Store database credentials in a .env file, read at runtime via python-dotenv. Never hardcode credentials in source code.

**Alternatives considered:** Hardcoded values in app.py (original state).

**Reason:** Hardcoded credentials in source code are a security risk. If the repository is ever made public or accidentally pushed, credentials are exposed. Environment files stay on the server and are excluded from Git via .gitignore.

---

## 2026-05-25 - Environment variable naming convention: PREFIX_VARIABLE

**Decision:** Prefix environment variables with the database name they belong to. Example: GRIDDB_HOST.

**Alternatives considered:** Generic names like DB_HOST.

**Reason:** As the project grows, multiple databases may exist. Prefixed names make it clear which credentials belong to which database and keep the .env file self-documenting.

---

## 2026-05-25 - Arch Linux on VPS, Fedora on ThinkPad

**Decision:** Run Arch Linux on the VPS and Fedora Workstation on the
ThinkPad development machine.

**Alternatives considered:** Fedora on both; Ubuntu on VPS.

**Reason:** Fedora was chosen for the ThinkPad because it supports Secure
Boot natively, which was required for the hardware. Arch was chosen for
the VPS because Secure Boot is irrelevant on a server, and Arch provides
a minimal, controllable environment with no unnecessary services.

---

## 2026-05-25 - Flask and Postgres not exposed publicly

**Decision:** Flask runs on 127.0.0.1:5000 and is only reachable via Nginx or WireGuard. Postgres is not exposed outside the VPS at all.

**Alternatives considered:** Exposing Flask directly on a public port.

**Reason:** Nginx acts as the single public entry point. This means SSL termination, rate limiting, and access control all happen in one place. Postgres has no business being reachable from the public internet.
