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

---

## Dispatchability and the balancing role of natural gas

Grid generation sources vary in how quickly they can respond to changes
in demand or renewable output.

**Natural gas** is the most dispatchable source — gas turbines can ramp
up or down within minutes. ERCOT uses NG as the primary balancing fuel,
absorbing variability from wind and solar in real time.

**Coal** is technically dispatchable but slow — plants take hours to ramp
meaningfully. In practice coal runs at relatively steady baseload output.

**Nuclear** runs at essentially constant output by design. It does not
participate in short-term balancing.

**Hydro** is flexible in principle but limited by water availability.
ERCOT has minimal hydro capacity.

**Wind and solar** are non-dispatchable — they generate whenever the
resource is available, regardless of grid needs.

The practical implication for stress analysis: NG ramp rate is the most
informative single signal for grid stress under renewable integration.
When solar drops at sunset or wind drops unexpectedly, NG absorbs the
gap. The magnitude and speed of NG ramp events measures how hard the
dispatchable fleet is being pushed.

Net load (total demand minus wind and solar) is the canonical metric
for this stress — it represents the residual demand that dispatchable
sources must serve. A steeper net load ramp means more stress.

---

## NG ramp rate as a grid stress signal

Large upward NG ramp events — hours where natural gas generation increases
rapidly — are the primary measurable stress signal in this dataset. They
occur in two main contexts:

**Winter evening ramps:** Solar drops to zero at sunset while heating
demand spikes. Gas must cover both simultaneously. These events cluster
at 17:00-19:00 in January and February and are growing in magnitude as
solar penetration increases year over year.

**Post-wind-event recovery:** When wind drops sharply after a high
generation period, gas must ramp up rapidly to replace it. The largest
single-hour NG ramps in the dataset (2019-2020) are morning recoveries
after overnight wind events pushed NG to near zero.

Large negative NG ramps (gas backing down fast) have two causes:
wind flooding the grid overnight, and solar morning ramp-up displacing
gas. These are generally routine dispatch events rather than stress
events, though they indicate increasing renewable integration pressure.

---
