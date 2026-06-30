---
inclusion: manual
---

# Generate AUTOSAR ARXML Knowledge Base (v2 — Indexed & Relationship-Aware)

## Purpose

Parse AUTOSAR ARXML files from a repository and generate a structured Markdown
knowledge base that a **Coding Agent can explore efficiently at scale**.

The primary consumer of this output is an AI agent answering questions like:

- "If I remove the rear-door module, what breaks?"
- "Which components depend on interface X?"
- "Trace the data flow from sensor S to the network bus."
- "What is the blast radius of de-contenting trim Y?"

To serve that consumer, this skill does more than dump one file per element. It
builds **global index files** and **structured, machine-parseable relationship
blocks** so the agent can compute dependency/blast-radius answers by reading a
few small index files instead of the entire knowledge base.

> Design principle: **Index first, detail on demand.** The agent should be able
> to answer "what is affected?" by reading only `_index/` files, then open the
> minimum set of detail files needed.

## Parameters

- **repo_path** (required): Path to the directory containing source `.arxml`
  files. All `.arxml` files in this directory (recursively) are parsed.
- **output_path** (required): Path where the knowledge base is written.

---

## Output Structure

Generate exactly this layout under `output_path`:

```
<output_path>/
├── README.md                       # Overview + generation metadata + how to navigate
├── _index/                         # Global, agent-first navigation layer
│   ├── path-index.md               # AUTOSAR path → file + type (resolve any reference)
│   ├── components.md               # All components: name, type, package, port counts, file
│   ├── interfaces.md               # All interfaces: name, type, #providers, #requesters, file
│   ├── platform-types.md           # All base/impl types: name, category, #consumers, file
│   ├── dependency-graph.md         # Forward + reverse adjacency lists (blast-radius core)
│   ├── port-map.md                 # Every component.port → interface + direction
│   ├── signal-chains.md            # End-to-end data-flow traces (runnable → … → I-PDU)
│   ├── composition-tree.md         # Hierarchical tree of all compositions
│   └── stats.md                    # Counts, unresolved refs, processing notes
├── components/
│   └── <ComponentName>.md          # One per SW component
├── interfaces/
│   └── <InterfaceName>.md          # One per interface
├── platform/
│   ├── BaseTypes.md                # All base types grouped
│   └── ImplementationDataTypes.md  # All impl data types + compu methods grouped
└── system/
    └── <SystemName>.md             # One per SYSTEM element (e.g. ECU_EXTRACT)
```

If two elements share a SHORT-NAME, disambiguate the filename by appending a
short hash or package suffix (e.g. `Door__Demo_Door.md`) and record both the
clean name and the disambiguated filename in `_index/path-index.md`.

---

## Element Classification

Parse each ARXML file and classify elements:

- **Components** — any SWC type:
  - `APPLICATION-SW-COMPONENT-TYPE`
  - `SERVICE-SW-COMPONENT-TYPE`
  - `COMPOSITION-SW-COMPONENT-TYPE`
  - `SENSOR-ACTUATOR-SW-COMPONENT-TYPE`
  - `COMPLEX-DEVICE-DRIVER-SW-COMPONENT-TYPE`
  - `ECU-ABSTRACTION-SW-COMPONENT-TYPE`
  - `NV-BLOCK-SW-COMPONENT-TYPE`
- **Interfaces** — any of:
  - `SENDER-RECEIVER-INTERFACE`
  - `CLIENT-SERVER-INTERFACE`
  - `MODE-SWITCH-INTERFACE`
  - `NV-DATA-INTERFACE`
  - `PARAMETER-INTERFACE`
  - `TRIGGER-INTERFACE`
- **Platform Types** — packages containing:
  - `SW-BASE-TYPE` → BaseTypes
  - `IMPLEMENTATION-DATA-TYPE` → ImplementationDataTypes
  - `COMPU-METHOD` → grouped with related types
  - `APPLICATION-PRIMITIVE-DATA-TYPE`, `APPLICATION-RECORD-DATA-TYPE` → ImplementationDataTypes
- **System** — `SYSTEM` elements (note CATEGORY, especially `ECU_EXTRACT`).
- **Communication** — `I-SIGNAL`, `SYSTEM-SIGNAL`, `I-SIGNAL-I-PDU`,
  `I-SIGNAL-TO-I-PDU-MAPPING`, `FRAME`, `CAN-CLUSTER`, etc. (captured in the
  system file and `signal-chains.md`, not as standalone files).

---

## Processing Procedure

The input may be **much larger than the demo** (thousands of components across
many files). Process in passes so context never overflows and the index is
always complete before details are written.

### Step 0: Plan Processing Batches

1. List all `.arxml` files under `repo_path` (recurse subdirectories).
2. Estimate total size (file count + line count).
3. Choose a mode:
   - **Small** (≤ ~10 files and ≤ ~5,000 total lines): single pass is fine.
   - **Large** (more): use the multi-pass flow below. Process detail files in
     batches of ~10 ARXML files (or ~5,000 lines) at a time.
4. Record the plan and counts in `_index/stats.md`.

### Step 1: First Pass — Lightweight Scan (build the skeleton index)

Scan every file extracting **only** the cheap identifying data — do NOT expand
full behavior yet:

- For each element: SHORT-NAME, element tag (type), UUID, full AUTOSAR path
  (built from nested `<AR-PACKAGE>/<SHORT-NAME>` ancestry), source filename.
- For each component: list of ports with `(port name, P/R, interface TREF path)`.
- For each interface: list of data elements / operations names only.
- For each composition: component prototypes and connector endpoints (path refs).
- For the system: implementation mappings and signal mappings (path refs).

From this pass, immediately write:

- `_index/path-index.md` (every AUTOSAR path → target file + type)
- `_index/components.md`
- `_index/interfaces.md`
- `_index/platform-types.md`
- `_index/port-map.md`

These index files let later passes resolve every cross-reference to a concrete
file without re-reading source XML.

### Step 2: Resolve the Relationship Graph

Using port interface references and composition connectors from Step 1, compute:

- **Forward dependencies**: for each component, which components it
  *requires from* (R-PORT consuming an interface a P-PORT provides) or *calls*
  (server call points). Resolve provider/consumer through composition assembly
  connectors when present; otherwise match by interface where the model is
  port-interface based.
- **Reverse dependencies**: invert the forward graph.
- **Composition containment**: parent composition → child instances.

Write `_index/dependency-graph.md` and `_index/composition-tree.md`.

### Step 3: Trace Signal / Data-Flow Chains

For each data element that flows out of the system or between components, build
an end-to-end chain by following:

```
runnable (write access)
  → data element (port + interface)
    → assembly/delegation connector
      → consumer runnable (read access)        [component-to-component hop]
      → system signal (signal mapping)          [if mapped to communication]
        → I-Signal (I-signal-to-system-signal)
          → I-PDU (I-signal-to-PDU mapping)
            → frame / cluster                    [if present]
```

Write all chains to `_index/signal-chains.md`. Each chain must name every hop
with its element name so the agent can cut the chain at any node and see the
downstream effect.

### Step 4: Second Pass — Generate Detail Files (batched)

For each batch of ARXML files, generate the full per-element detail files
(`components/`, `interfaces/`, `platform/`, `system/`) using the templates
below. Populate each component's structured **Dependencies** and **Impact Tags**
sections from the graph computed in Steps 2–3 (do not re-derive ad hoc).

### Step 5: Generate README + stats

Write `README.md` (navigation guide + metadata) and finalize `_index/stats.md`
with final counts and any unresolved references.

---

## Cross-Referencing Rules (apply everywhere)

- Always link by **relative Markdown link** to the target file, with the AUTOSAR
  path as the link text, e.g.
  `[/Demo/Door/Door](../components/Door.md)`.
- Preserve **all UUIDs and full AUTOSAR paths** verbatim for traceability.
- When a reference cannot be resolved (target not found in the input), write the
  raw path and tag it `(UNRESOLVED)`, and add it to `_index/stats.md`.
- Use tables for structured data; keep prose minimal and factual.
- If a section has no data, write `_None_`.
- Sort table rows alphabetically by name where practical (except ordered chains).

---

## Index File Templates

### `_index/path-index.md`

The master resolver: every AUTOSAR path → its file and type. The agent reads
this first to turn any reference (`/Demo/...`) into a file to open.

```markdown
# Path Index

Resolve any AUTOSAR path to its knowledge-base file.

| AUTOSAR Path | Type | File |
|--------------|------|------|
| /Demo/Door/Door | APPLICATION-SW-COMPONENT-TYPE | [components/Door.md](../components/Door.md) |
| /Demo/Interfaces/DoorStatus | SENDER-RECEIVER-INTERFACE | [interfaces/DoorStatus.md](../interfaces/DoorStatus.md) |
| /Demo/EDC/EDC | COMPOSITION-SW-COMPONENT-TYPE | [components/EDC.md](../components/EDC.md) |
| ... | ... | ... |
```

### `_index/components.md`

```markdown
# Component Index

| Component | Type | Package | P-Ports | R-Ports | File |
|-----------|------|---------|--------:|--------:|------|
| Door | APPLICATION | /Demo/Door | 2 | 0 | [Door.md](../components/Door.md) |
| DoorControl | APPLICATION | /Demo/DoorControl | 1 | 5 | [DoorControl.md](../components/DoorControl.md) |
| EDC | COMPOSITION | /Demo/EDC | 1 | 0 | [EDC.md](../components/EDC.md) |
| ... | ... | ... | | | ... |
```

### `_index/interfaces.md`

`Providers` = how many ports provide it; `Requesters` = how many require it.
High requester counts flag high-impact interfaces.

```markdown
# Interface Index

| Interface | Type | Providers | Requesters | File |
|-----------|------|----------:|-----------:|------|
| DoorStatus | SENDER-RECEIVER | 1 | 2 | [DoorStatus.md](../interfaces/DoorStatus.md) |
| DoorCommands | CLIENT-SERVER | 1 | 2 | [DoorCommands.md](../interfaces/DoorCommands.md) |
| ... | ... | | | ... |
```

### `_index/platform-types.md`

```markdown
# Platform Type Index

| Type | Category | Kind | Consumers | File |
|------|----------|------|----------:|------|
| uint8 | base | SW-BASE-TYPE | 4 | [BaseTypes.md](../platform/BaseTypes.md) |
| Boolean | impl | VALUE | 6 | [ImplementationDataTypes.md](../platform/ImplementationDataTypes.md) |
| ... | ... | ... | | ... |
```

### `_index/port-map.md`

Universal port lookup: every port in the system in one table.

```markdown
# Port Map

| Component.Port | Direction | Interface | Interface Type |
|----------------|-----------|-----------|----------------|
| Door.Status | P | /Demo/Interfaces/DoorStatus | SENDER-RECEIVER |
| Door.Command | P | /Demo/Interfaces/DoorCommands | CLIENT-SERVER |
| DoorControl.StatusLeft | R | /Demo/Interfaces/DoorStatus | SENDER-RECEIVER |
| ... | ... | ... | ... |
```

### `_index/dependency-graph.md`

The core blast-radius structure. Provide both directions.

```markdown
# Dependency Graph

## Forward Dependencies (what each component needs)

`Component → components it requires data/services from`

| Component | Depends On (via) |
|-----------|------------------|
| DoorControl | Door (StatusLeft, StatusRight, CommandsLeft, CommandsRight), IoHwAb (Led) |
| EDC | Door ×2, DoorControl, IoHwAb (containment) |
| Door | _None_ (leaf) |
| IoHwAb | _None_ (leaf) |

## Reverse Dependencies (blast radius — who breaks if this changes)

`Component → components that depend on it`

| Component | Depended On By |
|-----------|----------------|
| Door | DoorControl, EDC |
| DoorControl | EDC |
| IoHwAb | DoorControl, EDC |
| EDC | _None_ (root) |

## Interface Usage (who touches each interface)

| Interface | Provided By | Required By |
|-----------|-------------|-------------|
| DoorStatus | Door.Status | DoorControl.StatusLeft, DoorControl.StatusRight |
| DoorCommands | Door.Command | DoorControl.CommandsLeft, DoorControl.CommandsRight |
| ... | ... | ... |
```

### `_index/composition-tree.md`

```markdown
# Composition Tree

```
EDC  (COMPOSITION, root)
├── DoorLeft   : Door (APPLICATION)
├── DoorRight  : Door (APPLICATION)
├── Control    : DoorControl (APPLICATION)
└── IO         : IoHwAb (SERVICE)
```

| Instance | Type | Parent | File |
|----------|------|--------|------|
| DoorLeft | /Demo/Door/Door | EDC | [Door.md](../components/Door.md) |
| ... | ... | ... | ... |
```

### `_index/signal-chains.md`

```markdown
# Signal Chains (end-to-end data flow)

Each chain lists every hop. Cut at any node to see downstream impact.

## Chain: Door Lock Status (Left)

```
Door.DoorMain (runnable, write)
  → DoorStatus/Locked  [port: DoorLeft.Status]
    → connector: DoorLeft_Status_to_Control_StatusLeft
      → DoorControl.Main (read)  [port: Control.StatusLeft]
        → DoorControl.Main (write) CombinedStatus/LockedLeft
          → delegation: CombinedStatus_delegate_connector0 → EDC.CombinedStatus
            → system signal: CombinedStatusLockedLeftSSig
              → I-Signal: CombinedStatusLockedLeftISig
                → I-PDU: CombinedStatusLockedLeftIPdu
```

**Endpoints:** producer `Door` (instance DoorLeft) → network PDU `CombinedStatusLockedLeftIPdu`
**Cut analysis:** removing DoorLeft breaks this chain at the source; the PDU and
the CombinedStatus port lose this contribution.

## Chain: ... (repeat per traced data element)
```

### `_index/stats.md`

```markdown
# Knowledge Base Statistics

| Metric | Count |
|--------|------:|
| Source ARXML files | N |
| Total source lines | N |
| Components | N |
| Interfaces | N |
| Platform types | N |
| Systems | N |
| Signal chains traced | N |
| Unresolved references | N |

## Processing Mode
<small / large; number of batches>

## Unresolved References
| Path | Referenced From |
|------|-----------------|
| ... | ... |
```

---

## Detail File Templates

### Component (`components/<Name>.md`)

```markdown
# <ComponentName>

## Impact Tags

- **type:** <element tag>
- **safety-relevant:** <yes/no/unknown — yes if part of an ASIL-tagged path or named safety element>
- **network-connected:** <yes/no — yes if any data element reaches a system signal / I-PDU>
- **shared-implementation:** <impl name if reused by other instances, else No>
- **composition-parent:** <parent composition name(s) or None>
- **signal-producer:** <comma-separated system signals this component ultimately feeds, or None>
- **leaf:** <yes if no forward dependencies>

## Component Information

| Field | Value |
|-------|-------|
| Name | <SHORT-NAME> |
| Type | <element tag> |
| UUID | <UUID> |
| Package | <full AUTOSAR path> |
| Source File | <originating .arxml filename> |

## Description

<From DESC element if present; else a one-line factual summary from context.>

## Ports

### Provided Ports (P-PORT)

| Port Name | Interface | Interface Type | UUID |
|-----------|-----------|----------------|------|
| ... | [path](relative-link) | ... | ... |

### Required Ports (R-PORT)

| Port Name | Interface | Interface Type | UUID |
|-----------|-----------|----------------|------|
| ... | ... | ... | ... |

## Internal Behavior

| Field | Value |
|-------|-------|
| Name | <SHORT-NAME> |
| UUID | ... |
| Handle Termination | ... |
| Multiple Instantiation | ... |

## Events

| Event Name | Type | Trigger (Runnable) | Period | UUID |
|------------|------|--------------------|--------|------|
| ... | ... | ... | ... | ... |

## Runnables

### <RunnableName>

| Field | Value |
|-------|-------|
| UUID | ... |
| Symbol | ... |
| Minimum Start Interval | ... |
| Concurrent Invocation | ... |

**Data Read Access:** (if any)

| Access Name | Port | Data Element |
|-------------|------|--------------|
| ... | ... | ... |

**Data Write Access:** (if any)

| Access Name | Port | Data Element |
|-------------|------|--------------|
| ... | ... | ... |

**Server Call Points:** (if any)

| Call Point Name | Port | Operation | Timeout |
|-----------------|------|-----------|---------|
| ... | ... | ... | ... |

## Implementation

| Field | Value |
|-------|-------|
| Name | ... |
| UUID | ... |
| Programming Language | ... |
| Vendor ID | ... |
| Behavior Reference | ... |

## Dependencies

### Provides To

| Consumer Component | Via Port | Interface | Data Elements / Operations |
|--------------------|----------|-----------|----------------------------|
| ... | ... | ... | ... |

### Requires From

| Provider Component | Via Port | Interface | Data Elements / Operations |
|--------------------|----------|-----------|----------------------------|
| ... | ... | ... | ... |

### Calls (client → server)

| Target Component | Via Port | Operation |
|------------------|----------|-----------|
| ... | ... | ... |

### Called By (server ← client)

| Caller Component | Via Port | Operation |
|------------------|----------|-----------|
| ... | ... | ... |

### Participates In Signal Chains

| Chain | Role |
|-------|------|
| [<chain name>](../_index/signal-chains.md) | producer / relay / consumer |
```

For **COMPOSITION-SW-COMPONENT-TYPE**, also add:

```markdown
## Internal Components

| Instance Name | Component Type | Type Reference | UUID |
|---------------|----------------|----------------|------|
| ... | ... | [path](relative-link) | ... |

## Assembly Connectors

| Connector Name | Provider (Component.Port) | Requester (Component.Port) | UUID |
|----------------|---------------------------|----------------------------|------|
| ... | ... | ... | ... |

## Delegation Connectors

| Connector Name | Inner (Component.Port) | Outer Port | UUID |
|----------------|------------------------|------------|------|
| ... | ... | ... | ... |

## Architecture Diagram (Textual)

<ASCII block diagram of instances and connector data flow.>
```

### Interface (`interfaces/<Name>.md`)

```markdown
# <InterfaceName>

## Interface Information

| Field | Value |
|-------|-------|
| Name | <SHORT-NAME> |
| Type | <interface tag> |
| UUID | ... |
| Package | <full path> |
| Is Service | <true/false> |
| Source File | ... |

## Description

<Factual purpose.>

## Data Elements (Sender-Receiver)

| Element Name | Type | Implementation Policy | UUID |
|--------------|------|-----------------------|------|
| ... | [type](relative-link) | ... | ... |

## Operations (Client-Server)

### <OperationName>

| Field | Value |
|-------|-------|
| UUID | ... |

**Arguments:**

| Argument Name | Type | Direction | UUID |
|---------------|------|-----------|------|
| ... | ... | ... | ... |

**Possible Errors:** (if any)

| Error Name | Error Code | UUID |
|------------|------------|------|

## Usage (resolved from port-map / dependency-graph)

| Component | Port | Direction (P/R) |
|-----------|------|-----------------|
| ... | ... | ... |
```

### Platform — `platform/BaseTypes.md`

```markdown
# Platform Base Types

## Package Information

| Field | Value |
|-------|-------|
| Package | <path> |
| Category | <e.g. BLUEPRINT> |
| Source File | ... |
| AUTOSAR Schema | ... |

## Base Types

| Name | Size (bits) | Encoding | Native Declaration | Consumers | Description |
|------|-------------|----------|--------------------|----------:|-------------|
| ... | ... | ... | ... | N | ... |
```

### Platform — `platform/ImplementationDataTypes.md`

```markdown
# Implementation Data Types

## Package Information
...

## Value Types

| Name | Category | Base Type Reference | Type Emitter | Consumers |
|------|----------|---------------------|--------------|----------:|
| ... | ... | [base type](#) | ... | N |

## Pointer Types

| Name | Category | Target Type | Target Category | Const |
|------|----------|-------------|-----------------|-------|

## Computation Methods

### <name>
| Internal Value | Physical Value |
|----------------|----------------|
| ... | ... |
```

### System (`system/<Name>.md`)

```markdown
# <SystemName>

## System Information

| Field | Value |
|-------|-------|
| Name | ... |
| Type | SYSTEM |
| Category | <e.g. ECU_EXTRACT> |
| UUID | ... |
| Package | ... |
| Source File | ... |

## Root Software Composition

| Field | Value |
|-------|-------|
| Prototype Name | ... |
| UUID | ... |
| Composition Type | [path](relative-link) |

## Implementation Mappings

| Mapping Name | Component Instance | Implementation | UUID |
|--------------|--------------------|----------------|------|
| ... | [path](#) | [path](#) | ... |

## Signal Mappings

| Data Element | System Signal |
|--------------|---------------|
| ... | ... |

## System Signals

| Signal Name | UUID |
|-------------|------|
| ... | ... |

## Communication (I-Signals and I-PDUs)

| I-Signal Name | System Signal Reference | I-PDU Name |
|---------------|-------------------------|------------|
| ... | ... | ... |

## Notes

- <Factual observations: shared implementations, 1:1 mappings, etc.>
```

### `README.md` (output root)

```markdown
# <System> Knowledge Base

## How To Navigate (read this first)

This knowledge base is optimized for agent exploration. Start in `_index/`:

1. **Resolve a reference?** → `_index/path-index.md`
2. **What breaks if I change X?** → `_index/dependency-graph.md` (reverse section)
3. **Who uses interface/type X?** → `_index/interfaces.md`, `_index/dependency-graph.md`
4. **Trace data flow to the bus?** → `_index/signal-chains.md`
5. **Where does a port go?** → `_index/port-map.md`
6. **System hierarchy?** → `_index/composition-tree.md`

Only open detail files in `components/`, `interfaces/`, `platform/`, `system/`
after narrowing scope with the indexes.

## Overview

<Summary of the system described by the ARXML.>

## Source Files

| File | Description |
|------|-------------|
| ... | ... |

## Generation Details

| Field | Value |
|-------|-------|
| Generated by | <agent/model> |
| Generation date | <YYYY-MM-DD> |
| Method | Automated extraction from AUTOSAR ARXML |
| Input format | <schema versions found> |
| Output format | Indexed structured Markdown |

## Prompt Used

> <The triggering prompt.>

## Structure

<Directory tree listing.>

## Statistics

See [`_index/stats.md`](_index/stats.md).
```

---

## Rules Summary

- **Index first, detail on demand** — `_index/` must be complete and internally
  consistent before/independent of reading detail files.
- One Markdown file per component / interface / system element; platform types
  grouped into two files.
- Every cross-reference is a relative Markdown link with the AUTOSAR path as
  text. Preserve all UUIDs and paths verbatim.
- Relationship data in detail files is **populated from the computed graph**, not
  re-derived per file — keep it consistent with `_index/dependency-graph.md`.
- Use tables for structured data; `_None_` for empty sections.
- Tag unresolved references `(UNRESOLVED)` and list them in `_index/stats.md`.
- For large inputs, use the multi-pass batched flow so context never overflows.
- Do not modify source ARXML — this skill is strictly read-only.
