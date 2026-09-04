# Technology-Mapped Synthesis and STA Flow

This project deliberately separates generic RTL synthesis from characterized ASIC timing.
No frequency, WNS/TNS, cell area, or power value is reported unless an actual standard-cell
library and the corresponding tools are supplied.

## Technology-mapped synthesis

Set an absolute Liberty path and run:

```bash
export LIBERTY_FILE=/path/to/stdcells.lib
make asic
```

The flow uses Yosys, preferring `yosys-slang`, then runs `dfflibmap` and `abc -liberty`.
It writes:

```text
reports/synthesis/asic_mapped_synthesis_report.txt
reports/synthesis/superscalar_core_mapped.v
```

The mapped report may contain actual library cell counts/area only when this command succeeds.

## Static timing analysis

STA is opt-in because a clock constraint must not be invented. Supply either an SDC:

```bash
export LIBERTY_FILE=/path/to/stdcells.lib
export SDC_FILE=/path/to/core.sdc
make asic
```

or an explicit user-selected clock period:

```bash
export LIBERTY_FILE=/path/to/stdcells.lib
export CLOCK_PERIOD_NS=10
make asic
```

`CLOCK_PERIOD_NS=10` above is only an example command; it is **not** a project result or
recommended target. The script runs `sta`/`opensta` only when the constraint was explicitly
provided and writes:

```text
reports/timing/asic_sta_report.txt
```

## Current environment

The generation sandbox contains neither a characterized Liberty library nor Yosys/OpenSTA,
so technology mapping and STA remain **NOT RUN / TOOL UNAVAILABLE** here. This is intentional:
no MHz/WNS/TNS/area number is estimated from generic logic depth.
