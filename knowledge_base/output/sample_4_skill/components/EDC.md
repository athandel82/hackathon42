# EDC

## Impact Tags

- **type:** COMPOSITION-SW-COMPONENT-TYPE
- **safety-relevant:** unknown (no ASIL tagging present in the extract)
- **network-connected:** yes — its outer `CombinedStatus` port feeds all four `CombinedStatus*` system signals
- **shared-implementation:** No
- **composition-parent:** None (root composition; referenced by SYSTEM EDCEcuExtract via EDCPrototype)
- **signal-producer:** CombinedStatusLockedLeftSSig, CombinedStatusOpenLeftSSig, CombinedStatusLockedRightSSig, CombinedStatusOpenRightSSig
- **leaf:** no (contains Door, DoorControl, IoHwAb)

## Component Information

| Field | Value |
|-------|-------|
| Name | EDC |
| Type | COMPOSITION-SW-COMPONENT-TYPE |
| UUID | 034525f7-3ff6-33b2-a2b2-56321b03e240 |
| Package | /Demo/EDC |
| Source File | EcuExtract.arxml |
| Source Reference | EcuExtract.arxml:597 (/Demo/EDC/EDC) |

## Description

Electronic Door Control composition. Wires two `Door` instances and a `DoorControl`
to one another and to an `IoHwAb` service, and exposes the aggregated
`CombinedStatus` to the system for network mapping.

## Ports

### Provided Ports (P-PORT)

| Port Name | Interface | Interface Type | UUID | Source Ref |
|-----------|-----------|----------------|------|------------|
| CombinedStatus | [/Demo/Interfaces/CombinedStatus](../interfaces/CombinedStatus.md) | SENDER-RECEIVER | dc98dc78-1aca-36dd-9d98-e0a89fd18a21 | EcuExtract.arxml:600 |

### Required Ports (R-PORT)

_None_

## Internal Components

| Instance Name | Component Type | Type Reference | UUID | Source Ref |
|---------------|----------------|----------------|------|------------|
| DoorLeft | APPLICATION | [/Demo/Door/Door](Door.md) | 0d9d3407-5a9c-33f3-84b4-9080804a4ad0 | EcuExtract.arxml:606 |
| DoorRight | APPLICATION | [/Demo/Door/Door](Door.md) | 8b499a52-aea4-3b6a-a1bc-f52dbc9c776c | EcuExtract.arxml:610 |
| Control | APPLICATION | [/Demo/DoorControl/DoorControl](DoorControl.md) | 89c6bf8e-984f-376e-ad33-607d91e5a6ab | EcuExtract.arxml:614 |
| IO | SERVICE | [/Demo/Services/IoHwAb/IoHwAb](IoHwAb.md) | c4d885db-369c-3268-bdaf-521bdf1887ab | EcuExtract.arxml:618 |

## Assembly Connectors

| Connector Name | Provider (Component.Port) | Requester (Component.Port) | UUID | Source Ref |
|----------------|---------------------------|----------------------------|------|------------|
| DoorLeft_Command_to_Control_CommandsLeft | DoorLeft.Command | Control.CommandsLeft | a9c2b7f4-ee22-3bed-af64-d39c1194552a | EcuExtract.arxml:624 |
| DoorRight_Command_to_Control_CommandsRight | DoorRight.Command | Control.CommandsRight | b50acda8-1379-30f2-8b5b-9620a85276d1 | EcuExtract.arxml:638 |
| DoorLeft_Status_to_Control_StatusLeft | DoorLeft.Status | Control.StatusLeft | f297dc64-c381-377b-b5f5-06db999a09fb | EcuExtract.arxml:649 |
| DoorRight_Status_to_Control_StatusRight | DoorRight.Status | Control.StatusRight | ed1d8867-02cb-3bda-8263-3a2bbd9cb01e | EcuExtract.arxml:660 |
| IO_Digital_Led_to_Control_Led | IO.Digital_Led | Control.Led | d86f2f14-ec48-3159-ba69-d029e2628924 | EcuExtract.arxml:671 |

> Note: in the `*_Command_*` connectors, the `Door` (P-port `Command`) is the
> AUTOSAR connector "provider" of the client-server interface, and `Control`
> (R-port) is the "requester"/client that calls the operation.

## Delegation Connectors

| Connector Name | Inner (Component.Port) | Outer Port | UUID | Source Ref |
|----------------|------------------------|------------|------|------------|
| CombinedStatus_delegate_connector0 | Control.CombinedStatus | EDC.CombinedStatus | f7b45156-878a-3beb-895e-85845c887435 | EcuExtract.arxml:682 |

## Architecture Diagram (Textual)

```
                          ┌──────────────────────────────────────────┐
                          │                EDC (composition)          │
                          │                                           │
  DoorLeft (Door) ─Status─┼──► Control.StatusLeft                     │
                  ─Command┼──► Control.CommandsLeft (SetLock call)    │
                          │         │                                 │
 DoorRight (Door) ─Status─┼──► Control.StatusRight                    │
                  ─Command┼──► Control.CommandsRight (SetLock call)   │
                          │         │                                 │
        IO (IoHwAb) ─Led──┼──► Control.Led (Write call)               │
                          │         │                                 │
                          │   Control.CombinedStatus ─delegate─► EDC.CombinedStatus ──►
                          └──────────────────────────────────────────┘
                                                                        (→ system signals → I-PDUs)
```

## Dependencies

### Provides To

| Consumer Component | Via Port | Interface | Data Elements / Operations |
| --- | --- | --- | --- |
| SYSTEM EDCEcuExtract (signal mapping) | CombinedStatus | CombinedStatus | LockedLeft, OpenLeft, LockedRight, OpenRight |

### Requires From

_None_ (contains its dependencies internally)

### Contains (composition)

| Instance | Type |
| --- | --- |
| DoorLeft, DoorRight | [Door](Door.md) |
| Control | [DoorControl](DoorControl.md) |
| IO | [IoHwAb](IoHwAb.md) |

### Participates In Signal Chains

| Chain | Role |
| --- | --- |
| [Chain 1–4: CombinedStatus*](../_index/signal-chains.md) | delegation boundary (Control.CombinedStatus → EDC.CombinedStatus → system signals) |
