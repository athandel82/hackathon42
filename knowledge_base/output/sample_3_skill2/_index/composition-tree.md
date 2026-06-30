# Composition Tree

```
EDCEcuExtract  (SYSTEM, category ECU_EXTRACT)
└── EDCPrototype  (ROOT-SW-COMPOSITION-PROTOTYPE)
    └── EDC  (COMPOSITION, root)
        ├── DoorLeft   : Door         (APPLICATION)
        ├── DoorRight  : Door         (APPLICATION)
        ├── Control    : DoorControl  (APPLICATION)
        └── IO         : IoHwAb       (SERVICE)
```

| Instance | Type | Parent | File |
|----------|------|--------|------|
| EDCPrototype | /Demo/EDC/EDC | EDCEcuExtract (SYSTEM) | [EDCEcuExtract.md](../system/EDCEcuExtract.md) |
| DoorLeft | /Demo/Door/Door | EDC | [Door.md](../components/Door.md) |
| DoorRight | /Demo/Door/Door | EDC | [Door.md](../components/Door.md) |
| Control | /Demo/DoorControl/DoorControl | EDC | [DoorControl.md](../components/DoorControl.md) |
| IO | /Demo/Services/IoHwAb/IoHwAb | EDC | [IoHwAb.md](../components/IoHwAb.md) |

## Notes

- `DoorLeft` and `DoorRight` are two instances of the same `Door` type and share
  the implementation `/Demo/Door/DoorImplementation`.
- The `EDC` composition exposes a single outer port, `CombinedStatus`, delegated
  from `Control` (DoorControl).
