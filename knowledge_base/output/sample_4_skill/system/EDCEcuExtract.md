# EDCEcuExtract

## System Information

| Field | Value |
|-------|-------|
| Name | EDCEcuExtract |
| Type | SYSTEM |
| Category | ECU_EXTRACT |
| UUID | 76a90898-1abb-44ea-9f66-df8486e35a2e |
| Package | /Demo/EDC |
| Source File | EcuExtract.arxml |
| Source Reference | EcuExtract.arxml:694 (/Demo/EDC/EDCEcuExtract) |

## Description

ECU extract for the Electronic Door Control. Roots the [/Demo/EDC/EDC](../components/EDC.md)
composition via `EDCPrototype`, maps each contained instance to its implementation,
and maps the four `CombinedStatus` data elements to network system signals.

## Root Software Composition

| Field | Value |
|-------|-------|
| Prototype | EDCPrototype |
| UUID | 3c4ddf13-ba2f-4c58-a177-22e870fe2a3e |
| Composition Type | [/Demo/EDC/EDC](../components/EDC.md) |
| Source Reference | EcuExtract.arxml:782 |

## Implementation Mappings (SWC → Implementation)

| Mapping | Instance | Implementation | UUID | Source Ref |
|---------|----------|----------------|------|------------|
| DoorLeftMapping | DoorLeft | /Demo/Door/DoorImplementation | 9568678c-3676-46c1-a8bd-dff34a1935c7 | EcuExtract.arxml:698 |
| DoorRightMapping | DoorRight | /Demo/Door/DoorImplementation | 178ff4de-9526-48ef-baac-a3df23139594 | EcuExtract.arxml:698 |
| ControlMapping | Control | /Demo/DoorControl/DoorControlImplementation | e9229db9-7a9a-4c62-a1ea-616190f1fe26 | EcuExtract.arxml:698 |
| IOMapping | IO | /Demo/Services/IoHwAb/IoHwAbImpl | 5bfaf6df-ddc1-48d5-8501-0056103023e7 | EcuExtract.arxml:698 |

> The implementation mappings live inside the `ImplementationMappings`
> SYSTEM-MAPPING (EcuExtract.arxml:698). `DoorImplementation` is shared by both
> door instances.

## Signal Mappings (Data Element → System Signal)

Defined inside the `SignalMappings` SYSTEM-MAPPING (EcuExtract.arxml:743).

| Data Element (on EDC.CombinedStatus) | System Signal | Signal Source Ref |
|--------------------------------------|---------------|-------------------|
| [/Demo/Interfaces/CombinedStatus/LockedLeft](../interfaces/CombinedStatus.md) | CombinedStatusLockedLeftSSig | EcuExtract.arxml:793 |
| [/Demo/Interfaces/CombinedStatus/OpenLeft](../interfaces/CombinedStatus.md) | CombinedStatusOpenLeftSSig | EcuExtract.arxml:796 |
| [/Demo/Interfaces/CombinedStatus/LockedRight](../interfaces/CombinedStatus.md) | CombinedStatusLockedRightSSig | EcuExtract.arxml:799 |
| [/Demo/Interfaces/CombinedStatus/OpenRight](../interfaces/CombinedStatus.md) | CombinedStatusOpenRightSSig | EcuExtract.arxml:802 |

## Communication (System Signal → I-Signal → I-PDU)

| System Signal | I-Signal | I-Signal Src | I-PDU | I-PDU Src |
|---------------|----------|--------------|-------|-----------|
| CombinedStatusLockedLeftSSig | CombinedStatusLockedLeftISig | EcuExtract.arxml:810 | CombinedStatusLockedLeftIPdu | EcuExtract.arxml:814 |
| CombinedStatusOpenLeftSSig | CombinedStatusOpenLeftISig | EcuExtract.arxml:823 | CombinedStatusOpenLeftIPdu | EcuExtract.arxml:827 |
| CombinedStatusLockedRightSSig | CombinedStatusLockedRightISig | EcuExtract.arxml:836 | CombinedStatusLockedRightIPdu | EcuExtract.arxml:840 |
| CombinedStatusOpenRightSSig | CombinedStatusOpenRightISig | EcuExtract.arxml:849 | CombinedStatusOpenRightIPdu | EcuExtract.arxml:853 |

## Blast-Radius Notes

- This SYSTEM is the network boundary. Removing any `Door` instance or the
  `DoorControl` (`Control`) instance severs the corresponding `CombinedStatus*`
  chains at their source (see [_index/signal-chains.md](../_index/signal-chains.md)).
- The four I-PDUs are the externally observable artifacts; they carry no further
  frame/cluster mapping in this extract.
