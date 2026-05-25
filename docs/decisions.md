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

---

## 2026-05-25 - Generation table nullable values

**Decision:** value_mw is nullable

**Alternatives considered:** value_mw is not nullable

**Reason:** EIA occasionally reports null values for missing or unavailable hourly data.
Making value_mw NOT NULL would cause ingest to fail on otherwise valid rows.
Nulls are accepted and handled downstream in analysis.

---

## 2026-05-25 - Generation table unique values

**Decision:** unique constraint on (timestamp, respondent, fueltype)

**Alternatives considered:** no constraint

**Reason:** Prevents duplicate rows if the ingest script runs more than once over the
same time range. Postgres will reject the duplicate rather than silently
inserting it. The ingest script uses INSERT ... ON CONFLICT DO NOTHING to
handle this gracefully.

---

## 2026-05-25 - ERCOT backfill start date: 2019-01-01

**Decision:** Begin ERCOT historical backfill from 2019-01-01, the earliest date EIA-930 has reliable data for ERCOT.

**Alternatives considered:** Starting from 2024 (arbitrary recent date), starting from 2015 (EIA-930 launch, but no ERCOT data that early).

**Reason:** 2019 represents the complete available history for ERCOT in the EIA-930 dataset.

---

## 2026-05-25 — Backfill chunked by month

**Decision:** Pull historical data one month at a time rather than in one
request or by day.

**Alternatives considered:** Single large request (exceeds 5000 row API
limit), daily chunks (too many API calls).

**Reason:** One month of ERCOT data for 3 fuel types is approximately
2,200 rows, well within the 5000 row API limit. Monthly chunks balance
API efficiency with simplicity.

---

## 2026-05-25 — Separate backfill and ingest scripts

**Decision:** backfill_eia.py handles historical data, ingest_eia.py
handles ongoing pulls. Two separate scripts with different purposes.

**Alternatives considered:** One script that handles both cases.

**Reason:** Backfill runs once. Ingest runs on a schedule indefinitely.
Keeping them separate makes each script simpler and easier to reason about.
