# Dependency Graph

The core blast-radius structure. Dependencies are resolved through the `EDC`
composition's assembly connectors and from `DoorControl`'s server call points and
data accesses.

## Forward Dependencies (what each component needs)

`Component → components it requires data/services from`

| Component | Depends On (via) |
|-----------|------------------|
| Door | _None_ (leaf — only provides) |
| DoorControl | Door (StatusLeft, StatusRight via DoorStatus; CommandsLeft, CommandsRight via DoorCommands), IoHwAb (Led via DigitalServiceWrite) |
| EDC | Door ×2 (DoorLeft, DoorRight), DoorControl (Control), IoHwAb (IO) — by containment |
| IoHwAb | _None_ (leaf — only provides) |

## Reverse Dependencies (blast radius — who breaks if this changes)

`Component → components that depend on it`

| Component | Depended On By |
|-----------|----------------|
| Door | DoorControl, EDC |
| DoorControl | EDC |
| EDC | _None_ (root composition) |
| IoHwAb | DoorControl, EDC |

## Interface Usage (who touches each interface)

| Interface | Provided By | Required By |
|-----------|-------------|-------------|
| CombinedStatus | DoorControl.CombinedStatus, EDC.CombinedStatus (delegation) | _None_ (feeds system signals) |
| DigitalServiceWrite | IoHwAb.Digital_Led | DoorControl.Led |
| DoorCommands | Door.Command | DoorControl.CommandsLeft, DoorControl.CommandsRight |
| DoorStatus | Door.Status | DoorControl.StatusLeft, DoorControl.StatusRight |

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
