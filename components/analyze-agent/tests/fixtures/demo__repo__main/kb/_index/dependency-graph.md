# Dependency Graph

The core blast-radius structure. Dependencies are resolved through the `EDC`
composition's assembly connectors and from `DoorControl`'s server call points and
data accesses. Source refs point at the connector lines that establish each edge.

## Forward Dependencies (what each component needs)

`Component → components it requires data/services from`

| Component | Depends On (via) | Source Ref (connectors) |
|-----------|------------------|-------------------------|
| [/Demo/Door/Door](../components/Door.md) | _None_ (leaf — only provides) | — |
| [/Demo/DoorControl/DoorControl](../components/DoorControl.md) | Door (StatusLeft/StatusRight via DoorStatus; CommandsLeft/CommandsRight via DoorCommands), IoHwAb (Led via DigitalServiceWrite) | EcuExtract.arxml:624, EcuExtract.arxml:638, EcuExtract.arxml:649, EcuExtract.arxml:660, EcuExtract.arxml:671 |
| [/Demo/EDC/EDC](../components/EDC.md) | Door ×2 (DoorLeft, DoorRight), DoorControl (Control), IoHwAb (IO) — by containment | EcuExtract.arxml:606, EcuExtract.arxml:610, EcuExtract.arxml:614, EcuExtract.arxml:618 |
| [/Demo/Services/IoHwAb/IoHwAb](../components/IoHwAb.md) | _None_ (leaf — only provides) | — |

## Reverse Dependencies (blast radius — who breaks if this changes)

`Component → components that depend on it`

| Component | Depended On By |
|-----------|----------------|
| [/Demo/Door/Door](../components/Door.md) | DoorControl, EDC |
| [/Demo/DoorControl/DoorControl](../components/DoorControl.md) | EDC |
| [/Demo/EDC/EDC](../components/EDC.md) | _None_ (root composition) |
| [/Demo/Services/IoHwAb/IoHwAb](../components/IoHwAb.md) | DoorControl, EDC |

## Interface Usage (who touches each interface)

| Interface | Provided By | Required By |
|-----------|-------------|-------------|
| [/Demo/Interfaces/CombinedStatus](../interfaces/CombinedStatus.md) | DoorControl.CombinedStatus, EDC.CombinedStatus (delegation) | _None_ (feeds system signals) |
| [/Demo/Services/IoHwAb/DigitalServiceWrite](../interfaces/DigitalServiceWrite.md) | IoHwAb.Digital_Led | DoorControl.Led |
| [/Demo/Interfaces/DoorCommands](../interfaces/DoorCommands.md) | Door.Command | DoorControl.CommandsLeft, DoorControl.CommandsRight |
| [/Demo/Interfaces/DoorStatus](../interfaces/DoorStatus.md) | Door.Status | DoorControl.StatusLeft, DoorControl.StatusRight |

## Blast-Radius Quick Reference

- **Remove `Door`** → breaks `DoorControl` (loses StatusLeft/Right inputs and
  CommandsLeft/Right targets) and removes both `DoorLeft`/`DoorRight` instances
  from `EDC`. All 4 `CombinedStatus` signal chains lose their source.
- **Remove `IoHwAb`** → breaks `DoorControl.Led` server call (LED actuation lost);
  `DoorControl` status computation still functions.
- **Remove `DoorControl`** → `EDC.CombinedStatus` loses its provider; all 4 network
  signal chains (`CombinedStatus*`) are severed at the source.
- **Change `DoorStatus`/`DoorCommands`** → affects `Door` provider + both
  `DoorControl` requester ports (highest-fan-in interfaces).
- **`EDC`** is the root; nothing depends on it.
