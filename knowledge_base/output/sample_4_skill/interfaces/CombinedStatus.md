# CombinedStatus

## Interface Information

| Field | Value |
|-------|-------|
| Name | CombinedStatus |
| Type | SENDER-RECEIVER-INTERFACE |
| UUID | ac79088e-db77-300d-b6bf-72580349ffb0 |
| Package | /Demo/Interfaces |
| Is Service | false |
| Source File | EcuExtract.arxml |
| Source Reference | EcuExtract.arxml:364 (/Demo/Interfaces/CombinedStatus) |

## Description

Sender-receiver interface carrying the aggregated lock/open state for both doors.
Provided by `DoorControl.CombinedStatus`, delegated out of `EDC.CombinedStatus`,
and mapped element-by-element to the four `CombinedStatus*` system signals.

## Data Elements (Sender-Receiver)

| Element Name | Type | Implementation Policy | UUID | Source Ref |
|--------------|------|-----------------------|------|------------|
| LockedLeft | [/ArcCore/Platform/ImplementationDataTypes/boolean](../platform/ImplementationDataTypes.md) | STANDARD | a4fbcfbd-24e9-3222-9fbe-be25ac6e9740 | EcuExtract.arxml:368 |
| OpenLeft | [/ArcCore/Platform/ImplementationDataTypes/boolean](../platform/ImplementationDataTypes.md) | STANDARD | 080e1423-0f5b-3f2f-83e8-25b9c81d65ef | EcuExtract.arxml:379 |
| LockedRight | [/ArcCore/Platform/ImplementationDataTypes/boolean](../platform/ImplementationDataTypes.md) | STANDARD | 3c81145a-4f69-3436-8b28-a9edf9359d90 | EcuExtract.arxml:390 |
| OpenRight | [/ArcCore/Platform/ImplementationDataTypes/boolean](../platform/ImplementationDataTypes.md) | STANDARD | 6f5961a2-003e-3845-8369-62d2f365fa8c | EcuExtract.arxml:401 |

## Operations (Client-Server)

_None_

## Usage (resolved from port-map / dependency-graph)

| Component | Port | Direction (P/R) |
|-----------|------|-----------------|
| DoorControl | CombinedStatus | P |
| EDC | CombinedStatus | P (delegated outer port) |

## Signal Mapping

Each data element maps to a system signal (see [system/EDCEcuExtract.md](../system/EDCEcuExtract.md)):

| Data Element | System Signal |
|--------------|---------------|
| LockedLeft | [/Demo/EDC/SystemSignals/CombinedStatusLockedLeftSSig](../system/EDCEcuExtract.md) |
| OpenLeft | [/Demo/EDC/SystemSignals/CombinedStatusOpenLeftSSig](../system/EDCEcuExtract.md) |
| LockedRight | [/Demo/EDC/SystemSignals/CombinedStatusLockedRightSSig](../system/EDCEcuExtract.md) |
| OpenRight | [/Demo/EDC/SystemSignals/CombinedStatusOpenRightSSig](../system/EDCEcuExtract.md) |
