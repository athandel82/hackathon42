# Component Index

| Component | Type | Package | P-Ports | R-Ports | File |
|-----------|------|---------|--------:|--------:|------|
| Door | APPLICATION | /Demo/Door | 2 | 0 | [Door.md](../components/Door.md) |
| DoorControl | APPLICATION | /Demo/DoorControl | 1 | 5 | [DoorControl.md](../components/DoorControl.md) |
| EDC | COMPOSITION | /Demo/EDC | 1 | 0 | [EDC.md](../components/EDC.md) |
| IoHwAb | SERVICE | /Demo/Services/IoHwAb | 1 | 0 | [IoHwAb.md](../components/IoHwAb.md) |

## Notes

- `EDC` is the root composition; it instantiates `Door` twice (DoorLeft, DoorRight),
  `DoorControl` once (Control) and `IoHwAb` once (IO).
- `DoorControl` is the central application logic with the highest fan-in (5 R-ports).
