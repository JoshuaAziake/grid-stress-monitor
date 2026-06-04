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

## Duck curve endpoint averaging window

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
