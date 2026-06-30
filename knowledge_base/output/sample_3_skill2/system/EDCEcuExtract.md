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

## Root Software Composition

| Field | Value |
|-------|-------|
| Prototype Name | EDCPrototype |
| UUID | 3c4ddf13-ba2f-4c58-a177-22e870fe2a3e |
| Composition Type | [/Demo/EDC/EDC](../components/EDC.md) |

## Implementation Mappings

| Mapping Name | Component Instance | Implementation | UUID |
|--------------|--------------------|----------------|------|
| DoorLeftMapping | EDCPrototype/DoorLeft | [/Demo/Door/DoorImplementation](../components/Door.md) | 9568678c-3676-46c1-a8bd-dff34a1935c7 |
| DoorRightMapping | EDCPrototype/DoorRight | [/Demo/Door/DoorImplementation](../components/Door.md) | 178ff4de-9526-48ef-baac-a3df23139594 |
| ControlMapping | EDCPrototype/Control | [/Demo/DoorControl/DoorControlImplementation](../components/DoorControl.md) | e9229db9-7a9a-4c62-a1ea-616190f1fe26 |
| IOMapping | EDCPrototype/IO | [/Demo/Services/IoHwAb/IoHwAbImpl](../components/IoHwAb.md) | 5bfaf6df-ddc1-48d5-8501-0056103023e7 |

System mapping container UUID: 5911842c-0e9d-4e31-9302-a06b70855efc (ImplementationMappings)

> Note: `DoorLeft` and `DoorRight` both map to the single shared
> `DoorImplementation`.

## Signal Mappings

Container UUID: d2306cba-48e2-43d5-9378-888efc6ac72f (SignalMappings).
Each maps a `CombinedStatus` data element (on `EDC.CombinedStatus`) to a system signal.

| Data Element | System Signal |
|--------------|---------------|
| [/Demo/Interfaces/CombinedStatus/LockedLeft](../interfaces/CombinedStatus.md) | CombinedStatusLockedLeftSSig |
| [/Demo/Interfaces/CombinedStatus/OpenLeft](../interfaces/CombinedStatus.md) | CombinedStatusOpenLeftSSig |
| [/Demo/Interfaces/CombinedStatus/LockedRight](../interfaces/CombinedStatus.md) | CombinedStatusLockedRightSSig |
| [/Demo/Interfaces/CombinedStatus/OpenRight](../interfaces/CombinedStatus.md) | CombinedStatusOpenRightSSig |

## System Signals

Package: /Demo/EDC/SystemSignals (UUID 68c0ebba-6211-49fe-9ca1-5bc4468efdc7)

| Signal Name | UUID |
|-------------|------|
| CombinedStatusLockedLeftSSig | c4811a00-69c8-4728-917c-e457c27ff634 |
| CombinedStatusOpenLeftSSig | 14babacb-ba03-47e2-8ba9-082f5e96cb2e |
| CombinedStatusLockedRightSSig | 0fbdc633-0325-43a4-aad9-94a561e5641f |
| CombinedStatusOpenRightSSig | 225a0314-2688-42f9-8134-b0815975dd5e |

## Communication (I-Signals and I-PDUs)

Package: /Demo/EDC/Communication (UUID 5b8edb26-d0e2-4531-8838-b6afc177ec0c)

| I-Signal Name | System Signal Reference | I-PDU Name (I-SIGNAL-I-PDU) |
|---------------|-------------------------|------------------------------|
| CombinedStatusLockedLeftISig | CombinedStatusLockedLeftSSig | CombinedStatusLockedLeftIPdu |
| CombinedStatusOpenLeftISig | CombinedStatusOpenLeftSSig | CombinedStatusOpenLeftIPdu |
| CombinedStatusLockedRightISig | CombinedStatusLockedRightSSig | CombinedStatusLockedRightIPdu |
| CombinedStatusOpenRightISig | CombinedStatusOpenRightSSig | CombinedStatusOpenRightIPdu |

Each I-PDU contains a single `I-SIGNAL-TO-I-PDU-MAPPING` referencing its I-Signal:

| I-PDU | Mapping Name | I-Signal |
|-------|--------------|----------|
| CombinedStatusLockedLeftIPdu | CombinedStatusLockedLeftMapping | CombinedStatusLockedLeftISig |
| CombinedStatusOpenLeftIPdu | CombinedStatusOpenLeftMapping | CombinedStatusOpenLeftISig |
| CombinedStatusLockedRightIPdu | CombinedStatusLockedRightMapping | CombinedStatusLockedRightISig |
| CombinedStatusOpenRightIPdu | CombinedStatusOpenRightMapping | CombinedStatusOpenRightISig |

## Notes

- This is an **ECU extract** (CATEGORY=ECU_EXTRACT): a single-ECU view of the EDC
  composition with its communication mapping.
- All four `CombinedStatus` elements follow a 1:1 chain: data element → system
  signal → I-Signal → I-PDU. See [_index/signal-chains.md](../_index/signal-chains.md).
- No `FRAME` or `CAN-CLUSTER` is defined; chains terminate at the I-PDU.
- Only the `CombinedStatus` (sender side) is mapped to communication;
  `DoorStatus`, `DoorCommands`, and `DigitalServiceWrite` stay intra-ECU.
