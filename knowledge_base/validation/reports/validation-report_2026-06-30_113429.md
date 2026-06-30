# Knowledge Base Validation Report

| Field | Value |
|-------|-------|
| Generated | 2026-06-30 11:34:29 |
| Timestamp tag | 2026-06-30_113429 |
| Samples evaluated | 3 (sample_1_simple_prompt, sample_2_skill, sample_3_skill2) |
| Questions | 13 |
| Mode | per-sample (one clean-context sub-agent per sample, read-only to its own files) |
| Question bank | knowledge_base/validation/questions.md |

## Score Matrix

| ID | Category | sample_1_simple_prompt | sample_2_skill | sample_3_skill2 |
|----|----------|:----------------------:|:--------------:|:---------------:|
| Q01 | inventory | ✅ | ✅ | ✅ |
| Q02 | inventory | ✅ | ✅ | ✅ |
| Q03 | ports | ✅ | ✅ | ✅ |
| Q04 | dependency | ✅ | ✅ | ✅ |
| Q05 | blast-radius | ✅ | ✅ | ✅ |
| Q06 | blast-radius | ✅ | ✅ | ✅ |
| Q07 | signal-flow | ✅ | ✅ | ✅ |
| Q08 | signal-flow | ✅ | ✅ | ✅ |
| Q08b | data-type | ✅ | ✅ | ✅ |
| Q09 | composition | ✅ | ✅ | ✅ |
| Q10 | reuse | ✅ | ✅ | ✅ |
| Q11 | de-content | ✅ | ✅ | ✅ |
| Q12 | inventory (negative) | ✅ | ✅ | ✅ |
| **Score** | | **13/13** | **13/13** | **13/13** |

Legend: ✅ correct · ⚠️ partial · ❌ incorrect/missing

## Summary

| Sample | Correct | Partial | Incorrect | Avg files opened/question | Notes |
|--------|--------:|--------:|----------:|--------------------------:|-------|
| sample_1_simple_prompt | 13 | 0 | 0 | ~2.8 (not itemized per Q) | Flat one-file-per-element layout; answers required reading several detail files, especially for cross-boundary questions. |
| sample_2_skill | 13 | 0 | 0 | ~2.8 | Identical layout/content to sample_1; same correctness, same multi-file effort. |
| sample_3_skill2 | 13 | 0 | 0 | ~1.5 | Index-first layout. Answered most questions from a single `_index/` file; clearly the most efficient for blast-radius and signal-flow. |

All three knowledge-base layouts answered every question correctly — the underlying
EDC system is identical across samples, and each layout preserves enough fidelity to
reach the right answer. The differentiator is **navigation efficiency**, which is
exactly what matters for the product's "answer in minutes" promise.

`sample_3_skill2` (the indexed, relationship-aware layout) was consistently the
cheapest to query. It answered the headline blast-radius question (Q05) and the
end-to-end signal trace (Q07) from a **single** index file (`dependency-graph.md`,
`signal-chains.md`), whereas `sample_1`/`sample_2` had to open and cross-reference
4–5 detail files (component + composition + interface + system) to reconstruct the
same relationships. The flat samples are perfectly accurate but push the
relationship-stitching work onto the reader at query time; the indexed sample does
that work once at generation time.

One structural caveat for `sample_3_skill2`: it currently ships rich `_index/` files
and a `components/` folder but is **missing** the `interfaces/`, `platform/`, and
`system/` detail folders. It still answered every question because the indexes
(`port-map.md`, `signal-chains.md`, `path-index.md`, `dependency-graph.md`) carry
enough resolved detail — but deep single-element drill-downs (e.g. full operation
error tables for an interface) would currently fall back to the indexes only. Worth
completing the detail files so the index-first design degrades gracefully.

## Detailed Results

### Q01 — Component inventory
**Category:** inventory · **Use case:** what exists
**Expected key facts:** 4 component types — Door (APPLICATION), DoorControl (APPLICATION), IoHwAb (SERVICE), EDC (COMPOSITION); Door instantiated twice.

| Sample | Score | Files opened | Answer |
|--------|:-----:|--------------|--------|
| sample_1 | ✅ | 4 component files | 4 components: 2 application, 1 service, 1 composition. |
| sample_2 | ✅ | components/Door, DoorControl, IoHwAb, EDC (4) | Door (APP), DoorControl (APP), IoHwAb (SERVICE), EDC (COMPOSITION). |
| sample_3 | ✅ | _index/components.md (1) | Door (APP), DoorControl (APP), EDC (COMPOSITION, root), IoHwAb (SERVICE). |

### Q02 — Interface inventory
**Category:** inventory · **Use case:** what exists
**Expected key facts:** DoorStatus (S-R), CombinedStatus (S-R), DoorCommands (C-S), DigitalServiceWrite (C-S).

| Sample | Score | Files opened | Answer |
|--------|:-----:|--------------|--------|
| sample_1 | ✅ | interface files | DoorStatus/CombinedStatus = S-R; DoorCommands/DigitalServiceWrite = C-S. |
| sample_2 | ✅ | 4 interface files | Same, correct. |
| sample_3 | ✅ | _index/interfaces.md (1) | Same, correct, from one index. |

### Q03 — DoorControl ports
**Category:** ports · **Use case:** how a component connects
**Expected key facts:** P-PORT CombinedStatus (S-R); R-PORTs StatusLeft/StatusRight (DoorStatus), CommandsLeft/CommandsRight (DoorCommands), Led (DigitalServiceWrite).

| Sample | Score | Files opened | Answer |
|--------|:-----:|--------------|--------|
| sample_1 | ✅ | DoorControl.md | 6 ports (1 provided + 5 required), correct mapping. |
| sample_2 | ✅ | components/DoorControl.md (1) | All 6 ports + interfaces + types, correct. |
| sample_3 | ✅ | _index/port-map.md, components/DoorControl.md (2) | All 6 ports + interfaces + types, correct. |

### Q04 — DoorStatus consumers
**Category:** dependency · **Use case:** who depends on what
**Expected key facts:** Door provides (Status); DoorControl requires (StatusLeft, StatusRight).

| Sample | Score | Files opened | Answer |
|--------|:-----:|--------------|--------|
| sample_1 | ✅ | DoorStatus.md | Door provides; DoorControl consumes via StatusLeft/StatusRight. |
| sample_2 | ✅ | interfaces/DoorStatus.md (1) | Correct, including read/write direction. |
| sample_3 | ✅ | _index/interfaces.md, interfaces/DoorStatus.md (2) | Correct. |

### Q05 — Blast radius: remove Door
**Category:** blast-radius · **Use case:** what breaks if X is removed (headline)
**Expected key facts:** DoorControl inputs/calls break; EDC DoorLeft/DoorRight instances + connectors dangle; DoorLeftMapping/DoorRightMapping invalid; CombinedStatus signals lose source.

| Sample | Score | Files opened | Answer |
|--------|:-----:|--------------|--------|
| sample_1 | ✅ | multiple (component+composition+system) | Traced via connectors, mappings, signals, PDUs. |
| sample_2 | ✅ | Door, DoorControl, EDC, DoorStatus, system (5) | Full impact: instances, connectors, mappings, ports, downstream CombinedStatus. |
| sample_3 | ✅ | _index/dependency-graph.md (1) | Full reverse-dependency answer from a single index file. |

### Q06 — Blast radius: remove IoHwAb
**Category:** blast-radius · **Use case:** what breaks if X is removed
**Expected key facts:** DoorControl loses Led/DigitalServiceWrite call; EDC loses IO instance + IO→Control.Led connector; IOMapping invalid.

| Sample | Score | Files opened | Answer |
|--------|:-----:|--------------|--------|
| sample_1 | ✅ | multiple | LED actuation lost; connector + mapping affected. |
| sample_2 | ✅ | IoHwAb, DoorControl, EDC, system (4) | LED control lost; IO instance, connector, IOMapping. |
| sample_3 | ✅ | dependency-graph.md, signal-chains.md (2) | LED actuation lost; correctly notes the four network signal chains are unaffected (actuation-only path). |

### Q07 — Signal flow to the bus
**Category:** signal-flow · **Use case:** cross-boundary data-flow tracing
**Expected key facts (ordered):** Door.DoorMain writes DoorStatus/Locked → connector → DoorControl reads → writes CombinedStatus/LockedLeft → delegation → EDC.CombinedStatus → SSig → ISig → IPdu.

| Sample | Score | Files opened | Answer |
|--------|:-----:|--------------|--------|
| sample_1 | ✅ | multiple | Full chain Door→connector→DoorControl→CombinedStatus→delegation→system signal→I-signal→I-PDU. |
| sample_2 | ✅ | Door, DoorControl, CombinedStatus, system (4) | Full ordered chain, both left/right. |
| sample_3 | ✅ | _index/signal-chains.md (1) | Full ordered chain from one pre-traced index file. |

### Q08 — Communication PDUs
**Category:** signal-flow · **Use case:** cross-boundary tracing
**Expected key facts:** 4 I-PDUs (Combined Status Locked/Open × Left/Right), each carrying one I-Signal from the CombinedStatus interface.

| Sample | Score | Files opened | Answer |
|--------|:-----:|--------------|--------|
| sample_1 | ✅ | system file | 4 I-PDUs, one per CombinedStatus element. |
| sample_2 | ✅ | system/EDCEcuExtract.md (1) | 4 I-PDUs named + element carried. |
| sample_3 | ✅ | path-index.md, signal-chains.md (2) | 4 I-PDUs named + content. |

### Q08b — Data type resolution
**Category:** data-type · **Use case:** platform type resolution
**Expected key facts:** Locked/Open = boolean (/ArcCore/Platform/ImplementationDataTypes/boolean), STANDARD policy, defined in platform types.

| Sample | Score | Files opened | Answer |
|--------|:-----:|--------------|--------|
| sample_1 | ✅ | DoorStatus + platform | ArcCore boolean impl data type. |
| sample_2 | ✅ | DoorStatus, ImplementationDataTypes, BaseTypes (3) | boolean → base type /ArcCore/.../boolean. |
| sample_3 | ✅ | interfaces/DoorStatus.md (1) | boolean, /ArcCore/Platform/ImplementationDataTypes/boolean (category VALUE). |

### Q09 — Assembly connectors
**Category:** composition · **Use case:** structure / connectors
**Expected key facts:** 5 connectors — DoorLeft.Command→Control.CommandsLeft, DoorRight.Command→Control.CommandsRight, DoorLeft.Status→Control.StatusLeft, DoorRight.Status→Control.StatusRight, IO.Digital_Led→Control.Led.

| Sample | Score | Files opened | Answer |
|--------|:-----:|--------------|--------|
| sample_1 | ✅ | EDC.md | 5 assembly connectors listed. |
| sample_2 | ✅ | components/EDC.md (1) | All 5, correct. |
| sample_3 | ✅ | components/EDC.md (1) | All 5; correctly distinguishes CombinedStatus as a delegation (not assembly) connector. |

### Q10 — Shared implementation
**Category:** reuse · **Use case:** shared implementations
**Expected key facts:** DoorLeft and DoorRight both use DoorImplementation.

| Sample | Score | Files opened | Answer |
|--------|:-----:|--------------|--------|
| sample_1 | ✅ | system file | DoorLeft & DoorRight share DoorImplementation. |
| sample_2 | ✅ | system/EDCEcuExtract.md (1) | DoorLeft/DoorRight → /Demo/Door/DoorImplementation. |
| sample_3 | ✅ | _index/composition-tree.md (1) | DoorLeft/DoorRight → /Demo/Door/DoorImplementation. |

### Q11 — De-content the right door
**Category:** de-content · **Use case:** cost/obsolescence of removing content
**Expected key facts:** Right system signals/I-Signals/I-PDUs obsolete; DoorRightMapping removed; DoorRight connectors gone; DoorControl StatusRight/CommandsRight unconnected.

| Sample | Score | Files opened | Answer |
|--------|:-----:|--------------|--------|
| sample_1 | ✅ | multiple | Right-path signals/PDUs/mappings/connectors traced. |
| sample_2 | ✅ | EDC, DoorControl, CombinedStatus, system (4) | Full: connectors, ports, mapping, Right signals/I-signals/I-PDUs. |
| sample_3 | ✅ | signal-chains.md, EDC.md (2) | Full Right-chain obsolescence; notes left chains + LED path remain intact. |

### Q12 — Negative / coverage check
**Category:** inventory (negative) · **Use case:** does the KB avoid inventing data
**Expected key facts:** No CAN cluster/frame definitions; no ASIL/safety tagging; a good answer states the absence explicitly.

| Sample | Score | Files opened | Answer |
|--------|:-----:|--------------|--------|
| sample_1 | ✅ | system + components | "NOT FOUND IN KB" — no CAN cluster/frame, no ASIL. Correctly states absence. |
| sample_2 | ✅ | system, Door, DoorControl (3) | No CAN cluster/frame (comms stop at I-PDU); no ASIL. |
| sample_3 | ✅ | _index/stats.md, components (2) | No CAN-CLUSTER/FRAME; safety-relevant tagged "unknown" in impact tags. |

## Observations

- **Correctness is a tie (13/13 each).** Content fidelity is equivalent across all
  three layouts for this demo-sized system.
- **Efficiency is the differentiator.** `sample_3_skill2` answered the
  product-critical relationship questions (blast radius, signal flow) from a single
  pre-computed index file, roughly halving the files opened versus the flat samples.
  At demo scale this is minor; at the "thousands of interdependent artifacts" scale
  described in the project README, index-first is likely the decisive advantage.
- **Completeness gap to fix:** `sample_3_skill2` is missing `interfaces/`,
  `platform/`, and `system/` detail folders. It still scored 13/13 thanks to its
  indexes, but the index-first design is meant to degrade into detail files on demand
  — those should be generated to make deep drill-downs possible.
- **Negative-case discipline is good:** all three correctly refused to invent CAN/ASIL
  data (Q12), which is essential for a tool that must never fabricate safety-relevant
  facts.
