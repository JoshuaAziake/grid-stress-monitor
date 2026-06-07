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

## Network Topology

**Bus** - a node in the power network. Physically represents a substation
or a point where transmission lines, generators, and loads connect.
Every element in the network connects to a bus. Buses are numbered and
have a type:
- Type 1 (load bus / PQ bus): has fixed real and reactive power demand.
  Voltage magnitude and angle are solved by the power flow.
- Type 2 (generator bus / PV bus): has a generator maintaining a fixed
  voltage magnitude. Real power output is specified; voltage angle is solved.
- Type 3 (slack bus / reference bus): the single reference node for the
  whole network. Its voltage angle is fixed at zero by convention, giving
  all other angles something to be measured against. Also absorbs any
  mismatch between total generation and total load.

**Branch** - a connection between two buses. Represents either a
transmission line or a transformer. Has a resistance and reactance
(impedance), which determines how much power flows through it for a
given voltage angle difference. Branches have thermal limits — a maximum
MW flow before they overheat. Exceeding a branch limit is the failure
mode N-1 analysis looks for.

**Base MVA** - power systems equations are written in per-unit notation,
normalizing all quantities relative to a chosen base. The case118 base
is 100 MVA. This means a branch limit of 1.0 per-unit = 100 MW. Using
per-unit keeps the numbers well-conditioned for matrix arithmetic.

**baseKV** - the nominal voltage level of a bus. The IEEE 118-bus case
has two voltage levels: 138 kV and 345 kV. Transformers connect buses
at different voltage levels. DC power flow treats voltages as uniform
and ignores this distinction — it only matters for AC flow.

**N-1 Contingency** - a planning standard requiring that the grid remain
stable after the sudden loss of any single component (a transmission line,
transformer, or generator). If losing one element causes cascading failures,
the grid fails the N-1 standard.

In this project, N-1 screening works as follows: run a base-case DC power
flow to find flows on all branches. Then, for each branch in the network,
remove it and re-run the power flow. If any remaining branch now exceeds
its thermal limit, that contingency is flagged as a violation. With 186
branches in case118, this means 186 power flow solves per screening run.

**DC Power Flow** - a linearized approximation of the full AC power flow
equations. Assumes voltage magnitudes are constant and equal everywhere,
and that angle differences between buses are small. Under these assumptions
the power flow equations reduce to a linear system: P = B * theta, where
P is the vector of net injections (generation minus load) at each bus, B
is the network susceptance matrix (built from branch reactances), and theta
is the vector of unknown voltage angles. Solving this linear system gives
the angle at every bus, from which branch flows are calculated directly.
DC power flow cannot model reactive power, voltage magnitudes, or losses —
but it is accurate enough for contingency screening and is standard practice
in transmission planning.

**Susceptance Matrix (B matrix)** - the key data structure in DC power
flow. An NxN matrix where N is the number of buses. Diagonal entries are
the sum of susceptances of all branches connected to that bus. Off-diagonal
entry B[i][j] is the negative susceptance of the branch connecting bus i
to bus j, or zero if no direct branch exists. Built entirely from the
network topology and branch reactances. Inverting (or factoring) this
matrix is the main computational step in DC power flow.

---

## Case118 Data Dictionary

All quantities are in per-unit on a 100 MVA base unless otherwise noted.
Source: MATPOWER case118.m, IEEE 118-bus test case.

### mpc.bus columns

| Column | Name    | Units | Description                                              | Used? |
|--------|---------|-------|----------------------------------------------------------|-------|
| 1      | bus_i   | -     | Bus number (1-118). Primary key.                         | Yes   |
| 2      | type    | -     | 1=load, 2=generator (PV), 3=slack (reference)           | Yes   |
| 3      | Pd      | MW    | Real power demand (load) at this bus                     | Yes   |
| 4      | Qd      | MVAr  | Reactive power demand. AC only, ignored in DC flow.      | No    |
| 5      | Gs      | MW    | Shunt conductance. Ignored in DC flow.                   | No    |
| 6      | Bs      | MVAr  | Shunt susceptance. Ignored in DC flow.                   | No    |
| 7      | area    | -     | Area number. Not used in power flow.                     | No    |
| 8      | Vm      | pu    | Voltage magnitude. DC flow assumes 1.0 everywhere.       | No    |
| 9      | Va      | deg   | Voltage angle. This is what DC flow solves for.          | Yes*  |
| 10     | baseKV  | kV    | Nominal voltage (138 or 345 kV in this case).            | No    |
| 11     | zone    | -     | Loss zone. Not used in power flow.                       | No    |
| 12     | Vmax    | pu    | Maximum voltage limit. AC only.                          | No    |
| 13     | Vmin    | pu    | Minimum voltage limit. AC only.                          | No    |

*Va in the file is the solved value from the original AC power flow.
DC flow will solve for its own angles from scratch.

### mpc.gen columns

| Column | Name   | Units | Description                                              | Used? |
|--------|--------|-------|----------------------------------------------------------|-------|
| 1      | bus    | -     | Bus number this generator is connected to.               | Yes   |
| 2      | Pg     | MW    | Real power output.                                       | Yes   |
| 3      | Qg     | MVAr  | Reactive power output. AC only.                          | No    |
| 4      | Qmax   | MVAr  | Max reactive output. AC only.                            | No    |
| 5      | Qmin   | MVAr  | Min reactive output. AC only.                            | No    |
| 6      | Vg     | pu    | Voltage setpoint. AC only.                               | No    |
| 7      | mBase  | MVA   | Machine MVA base. Usually 100.                           | No    |
| 8      | status | -     | 1=in service, 0=out of service.                          | Yes   |
| 9      | Pmax   | MW    | Maximum real power output.                               | Yes   |
| 10     | Pmin   | MW    | Minimum real power output.                               | Yes   |
| 11-21  | ...    | -     | AGC, ramp rates, cost curve params. Not used here.       | No    |

### mpc.branch columns

| Column | Name   | Units | Description                                              | Used? |
|--------|--------|-------|----------------------------------------------------------|-------|
| 1      | fbus   | -     | "From" bus number.                                       | Yes   |
| 2      | tbus   | -     | "To" bus number.                                         | Yes   |
| 3      | r      | pu    | Resistance. Small in DC flow; often approximated as 0.   | No    |
| 4      | x      | pu    | Reactance. Susceptance = 1/x. Core of DC power flow.     | Yes   |
| 5      | b      | pu    | Line charging susceptance. AC only.                      | No    |
| 6      | rateA  | MW    | Thermal limit (normal). The N-1 violation threshold.     | Yes   |
| 7      | rateB  | MW    | Thermal limit (short-term emergency). Not used here.     | No    |
| 8      | rateC  | MW    | Thermal limit (emergency). Not used here.                | No    |
| 9      | ratio  | -     | Transformer tap ratio. 0 means transmission line.        | Yes   |
| 10     | angle  | deg   | Transformer phase shift. Usually 0.                      | No    |
| 11     | status | -     | 1=in service, 0=out of service.                          | Yes   |
| 12     | angmin | deg   | Min angle difference. Usually -360 (unconstrained).      | No    |
| 13     | angmax | deg   | Max angle difference. Usually 360 (unconstrained).       | No    |
