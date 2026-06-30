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

## Description

ECU Extract system configuration for the Electronic Door Control demo. Defines the root software composition, implementation mappings (which SWC implementation runs for each component instance), and signal mappings for communication.

## Root Software Composition

| Field | Value |
|-------|-------|
| Prototype Name | EDCPrototype |
| UUID | 3c4ddf13-ba2f-4c58-a177-22e870fe2a3e |
| Composition Type | /Demo/EDC/EDC |

## Implementation Mappings

| Mapping Name | Component Instance | Implementation | UUID |
|--------------|-------------------|----------------|------|
| ControlMapping | /Demo/EDC/EDC/Control | /Demo/DoorControl/DoorControlImplementation | e9229db9-7a9a-4c62-a1ea-616190f1fe26 |
| DoorLeftMapping | /Demo/EDC/EDC/DoorLeft | /Demo/Door/DoorImplementation | 9568678c-3676-46c1-a8bd-dff34a1935c7 |
| DoorRightMapping | /Demo/EDC/EDC/DoorRight | /Demo/Door/DoorImplementation | 178ff4de-9526-48ef-baac-a3df23139594 |
| IOMapping | /Demo/EDC/EDC/IO | /Demo/Services/IoHwAb/IoHwAbImpl | 5bfaf6df-ddc1-48d5-8501-0056103023e7 |

## Signal Mappings

### Sender-Receiver to System Signal

| Data Element | System Signal |
|--------------|---------------|
| CombinedStatus/LockedLeft | /Demo/EDC/SystemSignals/CombinedStatusLockedLeftSSig |
| CombinedStatus/LockedRight | /Demo/EDC/SystemSignals/CombinedStatusLockedRightSSig |
| CombinedStatus/OpenLeft | /Demo/EDC/SystemSignals/CombinedStatusOpenLeftSSig |
| CombinedStatus/OpenRight | /Demo/EDC/SystemSignals/CombinedStatusOpenRightSSig |

## System Signals

| Signal Name | UUID |
|-------------|------|
| CombinedStatusLockedLeftSSig | c4811a00-69c8-4728-917c-e457c27ff634 |
| CombinedStatusLockedRightSSig | 0fbdc633-0325-43a4-aad9-94a561e5641f |
| CombinedStatusOpenLeftSSig | 14babacb-ba03-47e2-8ba9-082f5e96cb2e |
| CombinedStatusOpenRightSSig | 225a0314-2688-42f9-8134-b0815975dd5e |

## Communication (I-Signals and I-PDUs)

| I-Signal Name | System Signal Reference | I-PDU Name |
|---------------|------------------------|------------|
| CombinedStatusLockedLeftISig | CombinedStatusLockedLeftSSig | CombinedStatusLockedLeftIPdu |
| CombinedStatusLockedRightISig | CombinedStatusLockedRightSSig | CombinedStatusLockedRightIPdu |
| CombinedStatusOpenLeftISig | CombinedStatusOpenLeftSSig | CombinedStatusOpenLeftIPdu |
| CombinedStatusOpenRightISig | CombinedStatusOpenRightSSig | CombinedStatusOpenRightIPdu |

## Notes

- Each I-Signal maps to exactly one System Signal
- Each I-PDU contains one I-Signal-to-PDU mapping
- All communication signals correspond to the CombinedStatus interface data elements
- Both DoorLeft and DoorRight use the same implementation (DoorImplementation), demonstrating reusable component types
