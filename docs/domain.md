# Grid Stress Monitor - Domain Knowledge

A growing glossary of power systems concepts relevant to this project.
Update this file whenever a new concept appears in the code or data.

---

## Organizations

**EIA** - Energy Information Administration. A US government agency that collects and publishes energy data. Primary data source for this project. Publishes hourly generation and demand data by RTO via a public API.

**ERCOT** - Electric Reliability Council of Texas. The RTO managing most of Texas. Operates independently from the rest of the US grid. Publishes its own real-time data in addition to reporting to EIA.

**RTO** - Regional Transmission Organization. An entity that manages the high-voltage electric transmission grid across a large geographic area. Coordinates movement of electricity from generators to consumers, keeping supply and demand balanced. Major US RTOs: ERCOT, PJM, MISO, CAISO, SPP, NYISO, ISO-NE.

---

## Grid Concepts

**Ramp Rate** - the speed at which a generator can increase or decrease its output, measured in MW per minute. Critical under high renewable penetration because solar and wind output can change rapidly, requiring other generators to ramp up or down quickly to compensate.

**Duck Curve** - a graph of net electricity demand (total demand minus renewable generation) over the course of a day. Named for its shape: demand dips in the middle of the day when solar is high, then ramps steeply in the evening when solar drops but demand remains high. The steep evening ramp is a grid stress indicator.

**Curtailment** - when a renewable generator (wind, solar) is forced to reduce output below what it could produce, because the grid cannot absorb all available generation. Indicates oversupply conditions and is a sign of grid stress from the opposite direction.

**Frequency Deviation** - the grid operates at a nominal frequency of 60 Hz (in NA). When generation and demand are balanced, frequency stays at 60 Hz. Imbalances cause frequency to deviate. Large deviations are a serious grid stress indicator.

**N-1 Contingency** - a planning standard requiring that the grid remain stable after the sudden loss of any single component (a transmission line, transformer, or generator). If losing one element causes cascading failures, the grid fails the N-1 standard. Contingency analysis will simulate these scenarios.

---

## Data

**Respondent** - EIA's term for a balancing authority or RTO reporting data. In the database, the respondent column contains codes like ERCOT, PJM, MISO that identify which entity reported the data.

**Balancing Authority** - an entity responsible for maintaining the real-time balance between generation and load within a defined area. RTOs are balancing authorities, but not all balancing authorities are RTOs - some utilities balance their own areas independently.
