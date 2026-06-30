# Validation Question Bank

Benchmark questions used by `skill.md` to evaluate each knowledge-base sample.
Questions are derived from the real use cases in the project `README.md`
(blast-radius, de-contenting cost/risk, cross-boundary tracing) plus basic
inventory questions that any knowledge base should answer.

All samples describe the **same** system — the Electronic Door Control (EDC)
demo — so the expected answers below are the ground truth for every sample.

> **Orchestrator only:** the "Expected key facts" are for scoring. They must
> **never** be shown to the answering sub-agent. The agent receives only the
> question text and its assigned sample directory.

Categories / use cases covered:

- `inventory` — what exists (components, interfaces, types)
- `ports` — how a component connects
- `dependency` — who depends on what (blast-radius core)
- `blast-radius` — what breaks if X is removed (the headline product question)
- `signal-flow` — end-to-end data flow to the bus (cross-boundary tracing)
- `data-type` — platform type resolution
- `composition` — structure / connectors
- `reuse` — shared implementations
- `de-content` — cost/obsolescence of removing content

---

## Q01 — Component inventory
**Category:** inventory
**Question:** How many software components are defined in this system, and what are their names and component types?
**Expected key facts:**
- 4 component *types*: `Door` (APPLICATION-SW-COMPONENT-TYPE), `DoorControl` (APPLICATION), `IoHwAb` (SERVICE-SW-COMPONENT-TYPE), `EDC` (COMPOSITION-SW-COMPONENT-TYPE).
- Door is instantiated twice (DoorLeft, DoorRight) inside EDC.

## Q02 — Interface inventory
**Category:** inventory
**Question:** What interfaces are defined, and what is the type (sender-receiver vs client-server) of each?
**Expected key facts:**
- `DoorStatus` — SENDER-RECEIVER
- `CombinedStatus` — SENDER-RECEIVER
- `DoorCommands` — CLIENT-SERVER
- `DigitalServiceWrite` — CLIENT-SERVER

## Q03 — Component ports
**Category:** ports
**Question:** What ports does the DoorControl component have, and which interface does each use?
**Expected key facts:**
- P-PORT: `CombinedStatus` → CombinedStatus (S-R).
- R-PORTs: `StatusLeft`, `StatusRight` → DoorStatus (S-R); `CommandsLeft`, `CommandsRight` → DoorCommands (C-S); `Led` → DigitalServiceWrite (C-S).

## Q04 — Interface consumers (dependency)
**Category:** dependency
**Question:** Which components use the DoorStatus interface, and as provider or consumer?
**Expected key facts:**
- `Door` provides it (via its `Status` port).
- `DoorControl` requires/consumes it (via `StatusLeft` and `StatusRight`).

## Q05 — Blast radius of removing Door
**Category:** blast-radius
**Question:** If I remove the Door component, which other components and elements are affected or break?
**Expected key facts:**
- `DoorControl` breaks: loses StatusLeft/StatusRight inputs (DoorStatus) and CommandsLeft/CommandsRight (DoorCommands SetLock) targets.
- `EDC` composition breaks: it contains DoorLeft and DoorRight instances; their assembly connectors (Status/Command to Control) become dangling.
- System `DoorLeftMapping` / `DoorRightMapping` implementation mappings become invalid.
- Downstream CombinedStatus signals lose their door-sourced values.

## Q06 — Blast radius of removing IoHwAb
**Category:** blast-radius
**Question:** What is the impact of removing the IoHwAb service component?
**Expected key facts:**
- `DoorControl` loses its `Led` server call to DigitalServiceWrite/Write (cannot drive the LED).
- `EDC` loses the `IO` instance and the `IO.Digital_Led → Control.Led` assembly connector.
- System `IOMapping` becomes invalid.

## Q07 — Signal flow to the bus
**Category:** signal-flow
**Question:** Trace the end-to-end data flow of a door's "Locked" status from where it is produced to the network/communication bus.
**Expected key facts (ordered chain):**
- `Door.DoorMain` writes `DoorStatus/Locked` on the Door `Status` port.
- Assembly connector carries it to `DoorControl.StatusLeft` (or StatusRight); DoorControl reads it.
- `DoorControl` writes `CombinedStatus/LockedLeft` (Main runnable).
- Delegation connector exposes it on `EDC.CombinedStatus`.
- Signal mapping → system signal `CombinedStatusLockedLeftSSig`.
- → I-Signal `CombinedStatusLockedLeftISig` → I-PDU `CombinedStatusLockedLeftIPdu`.

## Q08 — Communication PDUs
**Category:** signal-flow
**Question:** Which I-PDUs exist in this system and what do they carry?
**Expected key facts:**
- 4 I-PDUs: `CombinedStatusLockedLeftIPdu`, `CombinedStatusOpenLeftIPdu`, `CombinedStatusLockedRightIPdu`, `CombinedStatusOpenRightIPdu`.
- Each carries one I-Signal mapped to one system signal, all derived from the CombinedStatus interface data elements.

## Q08b — Data type resolution
**Category:** data-type
**Question:** What data type do the `Locked` and `Open` elements of the DoorStatus interface use, and where is that type defined?
**Expected key facts:**
- Both are `boolean`, resolved to `/ArcCore/Platform/ImplementationDataTypes/boolean`.
- Implementation policy STANDARD; defined in the platform base/implementation data types.

## Q09 — Composition connectors
**Category:** composition
**Question:** List the assembly connectors inside the EDC composition (provider port → requester port).
**Expected key facts (5 connectors):**
- DoorLeft.Command → Control.CommandsLeft
- DoorRight.Command → Control.CommandsRight
- DoorLeft.Status → Control.StatusLeft
- DoorRight.Status → Control.StatusRight
- IO.Digital_Led → Control.Led

## Q10 — Shared implementation (reuse)
**Category:** reuse
**Question:** Which component instances share the same implementation, and which implementation is it?
**Expected key facts:**
- `DoorLeft` and `DoorRight` both use `DoorImplementation` (the Door type is reused for both instances).

## Q11 — De-content the right door
**Category:** de-content
**Question:** If we remove the right door (the DoorRight instance), which signals, PDUs, mappings, and connections become obsolete or unconnected?
**Expected key facts:**
- System signals `CombinedStatusLockedRightSSig`, `CombinedStatusOpenRightSSig` lose their source.
- I-Signals `...LockedRightISig`, `...OpenRightISig` and I-PDUs `...LockedRightIPdu`, `...OpenRightIPdu` become obsolete.
- `DoorRightMapping` implementation mapping is removed.
- Assembly connectors `DoorRight.Command→Control.CommandsRight` and `DoorRight.Status→Control.StatusRight` disappear; DoorControl's `StatusRight`/`CommandsRight` ports become unconnected.

## Q12 — Negative / coverage check
**Category:** inventory
**Question:** Does this system contain any CAN cluster or frame definitions, and is any component marked safety-relevant (ASIL)?
**Expected key facts:**
- No CAN cluster/frame definitions are present in the model (communication stops at I-Signal/I-PDU level).
- No explicit ASIL / safety-relevance tagging is present; safety relevance is unknown/not stated.
- A good answer states the absence explicitly rather than inventing data.
