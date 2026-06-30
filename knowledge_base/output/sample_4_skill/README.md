# AUTOSAR ARXML Knowledge Base — EDC (Electronic Door Control)

Source-linked, self-validating knowledge base generated from the AUTOSAR ARXML in
`knowledge_base/input/autosar/ARXML`. Built for a coding agent answering
blast-radius questions ("if I remove X, what breaks?") with traceable provenance:
every fact carries a `file:line (sn_path)` source reference back to the XML.

## How to Navigate (index first, detail on demand)

Start in [`_index/`](_index/):

- [path-index.md](_index/path-index.md) — resolve any AUTOSAR path → KB file + source ref.
- [source-map.md](_index/source-map.md) — durable provenance (path/UUID → file:line).
- [components.md](_index/components.md) — all components.
- [interfaces.md](_index/interfaces.md) — all port interfaces.
- [platform-types.md](_index/platform-types.md) — base/implementation data types.
- [port-map.md](_index/port-map.md) — every port and the interface it carries.
- [dependency-graph.md](_index/dependency-graph.md) — forward/reverse deps + blast radius.
- [composition-tree.md](_index/composition-tree.md) — containment hierarchy.
- [signal-chains.md](_index/signal-chains.md) — end-to-end data-flow chains.
- [stats.md](_index/stats.md) — counts + validation summary.

Then open the per-element detail files under [`components/`](components/),
[`interfaces/`](interfaces/), [`platform/`](platform/), and [`system/`](system/).

## Model Summary

- **System:** [EDCEcuExtract](system/EDCEcuExtract.md) (ECU_EXTRACT), rooting the `EDC` composition.
- **Components:** [Door](components/Door.md) (×2 instances), [DoorControl](components/DoorControl.md),
  [IoHwAb](components/IoHwAb.md), [EDC](components/EDC.md) (composition).
- **Interfaces:** [DoorStatus](interfaces/DoorStatus.md), [DoorCommands](interfaces/DoorCommands.md),
  [CombinedStatus](interfaces/CombinedStatus.md), [DigitalServiceWrite](interfaces/DigitalServiceWrite.md).
- **Network:** four `CombinedStatus*` system signals → I-Signals → I-PDUs.

## Source Files

| File | Lines | Contains |
|------|------:|----------|
| EcuExtract.arxml | 869 | Components, interfaces, composition, system, signals, PDUs |
| ArcCore_Types.arxml | 523 | Platform base types, implementation data types, compu-methods |

## Validation

This knowledge base ships with `validate_kb.py`, which verifies every
cross-reference (markdown links, AUTOSAR paths, and source-ARXML line refs) and
can auto-repair mechanical breakage.

```bash
# Validate only (exit code 0 = clean, 1 = issues found)
python validate_kb.py . --source <path-to-source-arxml-dir>

# Validate and auto-fix repairable issues, then re-validate
python validate_kb.py . --source <path-to-source-arxml-dir> --fix
```

See [`_index/stats.md`](_index/stats.md) for the latest validation summary.
