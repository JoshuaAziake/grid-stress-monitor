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

---

## 2026-05-25 — Systemd unit files committed as reference copies

**Decision:** Copy eia-ingest.service and eia-ingest.timer into systemd/
in the project repo for documentation purposes.

**Alternatives considered:** Not committing them (authoritative files only
in /etc/systemd/system/). Using Ansible to manage system configuration.

**Reason:** Documentation value outweighs the downsides for a project at
this scale. Authoritative files remain in /etc/systemd/system/ — the
copies in systemd/ are reference only and must be noted as such in the
README when it is written. Ansible is a future consideration if the
project scales to multiple servers.

---

## 2026-06-04 — Ingest all fuel types rather than a hardcoded list

**Decision:** Removed the hardcoded `["WND", "SUN", "NG"]` fueltype filter
from both ingest_eia.py and backfill_eia.py. The API now fetches all fuel
types for a given respondent by omitting the facets[fueltype][] parameter.

**Alternatives considered:** Maintaining a whitelist of known fuel types.
Specifying only the new fuel types to add.

**Reason:** Partial generation data (only 3 of 9 fuel types) produces
misleading analysis — total generation sums were incomplete, distorting
ramp rate calculations. Fetching all types is more robust and picks up new
categories automatically; this was confirmed when BAT (battery storage) and
UES appeared in the backfill without any explicit configuration. A temporary
exclusion filter was added to backfill_eia.py to skip already-loaded types
during the one-time historical backfill.

---

## 2026-06-04 — Data quality: missing fuel type rows at month boundaries

**Decision:** Documented as a known data quality issue. Certain hours —
consistently at month boundaries — have missing rows for some fuel types
in the EIA source data. This causes SUM(value_mw) to undercount total
generation at those hours, producing large artificial negative deltas in
ramp rate calculations.

**Alternatives considered:** Treating as real grid events (incorrect).

**Reason:** Confirmed by inspection: 2024-09-30 19:00 shows only NG, SUN,
WND present while surrounding hours have all 7 fuel types. The artifact
signature is missing rows rather than zero values, causing sum-based
calculations to be unreliable at those timestamps.

---

## 2026-06-04 — Ramp rate filtering based on fuel type availability

**Decision:** Filter out hours where the reporting fuel type count is below
the expected count for that era before computing ramp rates. Three eras
defined by fuel type availability: pre-2019-01-02 (3 types: WND, SUN, NG),
2019-01-02 to 2024-11-07 (7 types: add COL, NUC, WAT, OTH), post-2024-11-07
(8+ types: add BAT and briefly UES).

**Alternatives considered:** Hardcoding a single minimum threshold. Excluding
month-boundary hours entirely.

**Reason:** Threshold tied to known availability windows is more principled
than an arbitrary cutoff and correctly handles the dataset's evolution over
time.

---

## 2026-06-04 — Duck curve endpoint averaging window

**Decision:** The `/api/duck-curve` endpoint averages hourly generation profiles
across the caller-supplied date range without any internal year-by-year breakdown.
The caller is responsible for keeping the window tight and temporally meaningful
(e.g. a single season or year).

**Alternatives considered:** Adding a `year` parameter that returns one profile per
calendar year in a single response, making year-over-year comparison explicit and
preventing accidental multi-year averaging.

**Reason:** A wide range spanning multiple years produces a profile dominated by
earlier years when solar capacity was lower, understating current solar penetration.
Keeping windows tight avoids this. The single-parameter approach is simpler and
already correct — the year parameter option is deferred as a future enhancement
if the frontend needs side-by-side annual comparisons.

---

##  2026-06-04 — HTTPS with self-signed certificate

**Decision:** Use a self-signed TLS certificate generated with `openssl req -x509`
for HTTPS on the VPS.

**Alternatives considered:** Let's Encrypt / Certbot for a trusted certificate.
Requires a domain name — not available on a raw IP address. Deferred until a
domain is added to the project.

**Reason:** A self-signed cert provides encrypted transport without requiring a
domain. Browsers show a security warning on first visit which must be clicked
through once. Acceptable for a personal project on a raw IP. The certificate
expires in 365 days and must be regenerated manually, or replaced with a
Let's Encrypt cert if a domain is added. Cert lives at
`/etc/ssl/certs/grid-stress-monitor.crt`, key at
`/etc/ssl/private/grid-stress-monitor.key`.

---

##  2026-06-04 — Frontend served from /srv/, not directly from repo

**Decision:** Serve frontend files from `/srv/grid-stress-monitor/frontend/`
with a symlink at `/var/www/grid-stress-monitor`. A deploy script
(`scripts/deploy_frontend.sh`) copies from the repo to `/srv/` when changes
are ready to publish.

**Alternatives considered:** Serving directly from the repo via a symlink at
`/var/www/grid-stress-monitor -> /home/joshua/grid-stress-monitor/frontend`.
Rejected because `/home/joshua/` has `700` permissions — Nginx runs as `nobody`
and cannot traverse the home directory.

**Reason:** `/srv/` is world-readable and the conventional location for
system-served data on Linux. Separating the working copy (repo) from the
serving location (`/srv/`) also follows standard deployment practice — the
deploy script is the explicit publishing step. Workflow: edit in repo, commit,
run `scripts/deploy_frontend.sh` to publish.

---

## 2026-06-05 - Keep current SQL queries in Python script

**Decision:** Keep duck curve, ramp rate, and renewable penetration analytics in SQL via Flask. Do not reimplement in C++.

**Alternatives considered:** Reimplement aggregation logic in C++ using libpq, fetching raw rows from Postgres and computing averages and distributions in compiled code.

**Reason:** At current and projected data volumes, Postgres handles these aggregations in milliseconds. SQL is the right tool for set-based aggregation — moving it to C++ would be premature optimization with no meaningful performance gain. C++ enters the project in Phase F for DC power flow and N-1 contingency screening, computations that SQL cannot perform at all. Keeping the boundary clean — SQL for aggregation, C++ for numerical methods — makes the architecture easier to reason about and avoids introducing complexity without justification.

---

## 2026-06-07

**Decision:** Store network topology tables (buses, branches, generators) in a
dedicated `network` Postgres schema rather than the default `public` schema.

**Alternatives considered:** Adding all tables to `public` alongside the existing
`generation` table.

**Reason:** The two data categories are fundamentally different in nature.
`public.generation` is time-series operational data ingested hourly from EIA.
`network.buses`, `network.branches`, `network.generators` are static topology
loaded once from the IEEE 118-bus test case. Keeping them in separate schemas
makes that distinction explicit and prevents the database from becoming an
undifferentiated pile of tables as the project grows.

---

## 2026-06-07

**Decision:** Grant flask user USAGE on the network schema and INSERT/SELECT
on its tables and sequences, rather than running the parser as the postgres
superuser.

**Alternatives considered:** Running parse_case118 as postgres directly.

**Reason:** The app should never connect as a superuser. Explicit grants give
flask exactly the permissions it needs and nothing more. This is consistent
with the principle of least privilege and the existing pattern for the
public schema.

---
