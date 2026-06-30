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

## Description

Aggregated lock/open status for both doors. Provided by `DoorControl` and
delegated out of the `EDC` composition; each data element is mapped to a network
system signal in the ECU extract.

## Data Elements (Sender-Receiver)

| Element Name | Type | Implementation Policy | UUID |
|--------------|------|-----------------------|------|
| LockedLeft | [/ArcCore/Platform/ImplementationDataTypes/boolean](../platform/ImplementationDataTypes.md) | STANDARD | a4fbcfbd-24e9-3222-9fbe-be25ac6e9740 |
| OpenLeft | [/ArcCore/Platform/ImplementationDataTypes/boolean](../platform/ImplementationDataTypes.md) | STANDARD | 080e1423-0f5b-3f2f-83e8-25b9c81d65ef |
| LockedRight | [/ArcCore/Platform/ImplementationDataTypes/boolean](../platform/ImplementationDataTypes.md) | STANDARD | 3c81145a-4f69-3436-8b28-a9edf9359d90 |
| OpenRight | [/ArcCore/Platform/ImplementationDataTypes/boolean](../platform/ImplementationDataTypes.md) | STANDARD | 6f5961a2-003e-3845-8369-62d2f365fa8c |

## Operations (Client-Server)

_None_

## Usage (resolved from port-map / dependency-graph)

| Component | Port | Direction (P/R) |
|-----------|------|-----------------|
| DoorControl | CombinedStatus | P |
| EDC | CombinedStatus | P (outer, via delegation) |

## Signal Mapping

| Data Element | System Signal |
|--------------|---------------|
| LockedLeft | CombinedStatusLockedLeftSSig |
| OpenLeft | CombinedStatusOpenLeftSSig |
| LockedRight | CombinedStatusLockedRightSSig |
| OpenRight | CombinedStatusOpenRightSSig |

See [system/EDCEcuExtract.md](../system/EDCEcuExtract.md) and
[_index/signal-chains.md](../_index/signal-chains.md) for the full data flow to
the I-PDUs.
