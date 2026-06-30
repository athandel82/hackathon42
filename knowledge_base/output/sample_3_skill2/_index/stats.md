# Knowledge Base Statistics

| Metric | Count |
|--------|------:|
| Source ARXML files | 2 |
| Total source lines | 1,392 |
| Components | 4 |
| Interfaces | 4 |
| Platform base types | 10 |
| Platform implementation data types | 11 (ArcCore) + 11 (AUTOSAR duplicate) + 3 (Demo/IoHwAb) |
| Compu methods | 3 |
| Systems | 1 |
| System signals | 4 |
| I-Signals | 4 |
| I-PDUs (I-SIGNAL-I-PDU) | 4 |
| Signal chains traced | 4 (network) + 3 (command/actuation control paths) |
| Unresolved references | 0 |

## Processing Mode

**Small** — 2 ARXML files, 1,392 total lines. Single pass; no batching required.

| File | Lines | Schema |
|------|------:|--------|
| EcuExtract.arxml | 869 | autosar_4-1-1.xsd (r4.0) |
| ArcCore_Types.arxml | 523 | autosar_4-0-3.xsd (r4.0) |

## Unresolved References

| Path | Referenced From |
|------|-----------------|
| _None_ | — |

All `TREF`/`REF` targets (interface refs, type refs, behavior refs, signal refs,
implementation refs) resolved to elements present in the input.

## Processing Notes

- The `/AUTOSAR/Platform/ImplementationDataTypes` package in `ArcCore_Types.arxml`
  duplicates the standard platform types but is not referenced by any application
  element; the model consistently uses the `/ArcCore/Platform/...` set.
- `Door` is instantiated twice inside `EDC` (DoorLeft, DoorRight) and both map to
  the single shared implementation `/Demo/Door/DoorImplementation`.
- No `FRAME`, `CAN-CLUSTER`, or PDU-to-frame mapping is present; signal chains
  terminate at the I-PDU level.
